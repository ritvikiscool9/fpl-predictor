import types

from src.database import update_player_prices


class FakeTableUpdate:
    def __init__(self, name, supabase):
        self.name = name
        self.supabase = supabase
        self._last_update = None
        self._last_eq = None

    def select(self, *args, **kwargs):
        return self

    def execute(self):
        # For select('id, fpl_player_id') return mapping
        if self.name == "players":
            return types.SimpleNamespace(data=self.supabase._players)
        # For update calls return a fake data list to indicate rows updated
        if self._last_update is not None:
            # store the update for assertion
            db_id = self._last_eq
            self.supabase.updated.setdefault(db_id, []).append(self._last_update)
            return types.SimpleNamespace(data=[{"updated": True}])
        return types.SimpleNamespace(data=[])

    def update(self, payload):
        self._last_update = payload
        return self

    def eq(self, column, value):
        # capture the db player id used in .eq('player_id', db_player_id)
        self._last_eq = value
        return self


class FakeSupabaseUpdate:
    def __init__(self, players_mapping):
        # players_mapping: list of dicts with fpl_player_id and id
        self._players = players_mapping
        self.updated = {}

    def table(self, name):
        return FakeTableUpdate(name, self)


def test_update_player_prices_normalizes_and_skips_out_of_range(monkeypatch):
    # Prepare fake supabase client with 3 players
    players_mapping = [
        {"fpl_player_id": 10, "id": 101},
        {"fpl_player_id": 11, "id": 102},
        {"fpl_player_id": 12, "id": 103},
    ]
    fake_supabase = FakeSupabaseUpdate(players_mapping)

    # Monkeypatch get_supabase_client used in the module
    monkeypatch.setattr(
        update_player_prices, "get_supabase_client", lambda: fake_supabase
    )

    # Create an updater and monkeypatch its get_current_fpl_data to return test rows
    updater = update_player_prices.PlayerPriceUpdater()

    test_fpl_players = [
        {
            "id": 10,
            "now_cost": 4.5,
            "selected_by_percent": "12.3",
        },  # should normalize to 45
        {"id": 11, "now_cost": 45, "selected_by_percent": "5.0"},  # stays 45
        {
            "id": 12,
            "now_cost": 200,
            "selected_by_percent": "0",
        },  # out of range -> skipped
    ]

    monkeypatch.setattr(updater, "get_current_fpl_data", lambda: test_fpl_players)

    # Run update
    updater.update_player_prices()

    # Ensure updates were made and out-of-range player skipped
    # db id 101 and 102 should have updates recorded
    assert 101 in fake_supabase.updated
    assert 102 in fake_supabase.updated
    # 103 (player id 12) should not have been updated
    assert 103 not in fake_supabase.updated

    # Check normalized now_cost for player 10 -> 45
    updates_101 = fake_supabase.updated[101]
    assert any(up.get("now_cost") == 45 for up in updates_101)

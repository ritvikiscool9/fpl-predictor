import types

from src.database import database_refresh


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


class FakeTable:
    def __init__(self, name, supabase):
        self.name = name
        self.supabase = supabase
        self._last_insert = None

    def select(self, *args, **kwargs):
        self._select_args = args
        return self

    def execute(self):
        # Return players list when selecting from players
        if self.name == "players":
            return types.SimpleNamespace(data=self.supabase._players_data)
        # For inserts return a simple object
        if self._last_insert is not None:
            return types.SimpleNamespace(data=self._last_insert)
        return types.SimpleNamespace(data=[])

    def insert(self, data):
        # capture insert data and pretend it succeeded
        self._last_insert = data
        # store inserted for test inspection
        self.supabase.inserted.setdefault(self.name, []).append(data)
        return self

    # simple no-op for methods used elsewhere
    def range(self, *a, **kw):
        return self

    def eq(self, *a, **kw):
        return self


class FakeSupabase:
    def __init__(self, players_ids):
        # players_ids: iterable of fpl_player_id ints
        self._players_data = [{"fpl_player_id": pid} for pid in players_ids]
        self.inserted = {}

    def table(self, name):
        return FakeTable(name, self)


def test_refresh_player_performances_preloads_and_skips_unknown(monkeypatch):
    # Prepare fake supabase with only player id 1 present
    fake = FakeSupabase(players_ids=[1])
    database_refresh.supabase = fake

    # Mock requests.get to return bootstrap-static then event/1/live
    def fake_get(url, *args, **kwargs):
        if url.endswith("bootstrap-static/"):
            # one finished GW with id=1
            return FakeResponse(200, {"events": [{"id": 1, "finished": True}]})
        elif "event/1/live/" in url:
            # elements include a known id (1) and an unknown id (99)
            return FakeResponse(
                200,
                {
                    "elements": [
                        {"id": 1, "stats": {"minutes": 90, "total_points": 5}},
                        {"id": 99, "stats": {"minutes": 10, "total_points": 0}},
                    ]
                },
            )
        return FakeResponse(404, {})

    monkeypatch.setattr(database_refresh.requests, "get", fake_get)

    refresher = database_refresh.FPLDatabaseRefresh()

    # Run only the player performance refresh (should insert only 1 player's data)
    refresher.refresh_player_performances_current_season()

    # Inspect inserted data captured by fake supabase
    inserted = fake.inserted.get("player_performances", [])
    # inserted may be nested lists depending on batching; flatten
    flattened = [
        item
        for batch in inserted
        for item in (batch if isinstance(batch, list) else [batch])
    ]

    # Should have inserted at least one record for player id 1 and none for 99
    assert any(rec.get("player_id") == 1 for rec in flattened)
    assert not any(rec.get("player_id") == 99 for rec in flattened)

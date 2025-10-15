# FPL Predictor AI Development Guide

Personal reference for implementing AI system to analyze FPL database and generate optimal teams.

## 🎯 Current Status

- ✅ Database fully populated (teams, players, fixtures, stats)
- ✅ Rule-based prediction system working
- ⏳ Need to implement ML models for better predictions

## 🗄️ Available Data in Database

### Tables & Data Volume

- **teams**: 20 Premier League teams with mappings
- **players**: 743 players with FPL + football-data mappings
- **gameweeks**: 38 gameweeks for 2025-26 season
- **fixtures**: 380 fixtures with results and difficulty ratings
- **current_player_stats**: Real-time stats for all 743 players
- **current_team_stats**: Team performance metrics
- **player_performances**: Historical performance data

### Key Data Points Available

- Player stats: goals, assists, minutes, points, price, ownership%
- Team metrics: wins, clean sheets, goals for/against
- Fixture data: difficulty ratings, home/away status
- Form indicators: recent performance trends

## 🤖 AI Implementation Steps

### Phase 1: Data Collection & Feature Engineering

#### 1.1 Historical Data Expansion

```python
# TODO: Create functions to collect 3-5 seasons of data
def collect_historical_gameweek_data():
    # Pull historical FPL data for seasons 2020-21 to 2024-25
    # Store in new table: historical_player_stats
    pass

def collect_historical_fixtures():
   # Get 3+ seasons of match results with context
    # Store in: historical_fixtures
    pass

def collect_injury_suspension_data():
    # Track injury/suspension patterns by player
    # Store in: player_availability_history
    pass
```

#### 1.2 Feature Engineering Functions

```python
# TODO: Create feature engineering pipeline
def create_rolling_averages():
    # 3, 5, 10 gameweek rolling averages for all metrics
    # Points, minutes, goals, assists, etc.
    pass

def create_form_indicators():
    # Trend analysis: improving/declining performance
    # Rate of change in key metrics
    pass

def create_matchup_features():
    # Historical performance vs specific opponents
    # Home/away split analysis
    pass

def create_contextual_features():
    # Days of rest, fixture congestion
    # European competition participation
    # International break effects
    pass

def create_team_strength_features():
    # Dynamic team strength ratings
    # Attack/defense ratings by period
    pass
```

### Phase 2: ML Model Development

#### 2.1 Data Preparation Pipeline

```python
# TODO: Create ML data pipeline
def prepare_training_data():
    """
    Steps:
    1. Combine all feature tables into training dataset
    2. Handle missing values and outliers
    3. Create target variables (next gameweek points)
    4. Split data chronologically (no future leakage)
    5. Feature selection and correlation analysis
    """
    pass

def create_position_datasets():
    """
    Create separate datasets for each position:
    - Goalkeepers (different scoring patterns)
    - Defenders (clean sheet focus)
    - Midfielders (balanced scoring)
    - Forwards (goal-heavy scoring)
    """
    pass
```

#### 2.2 Model Implementation

```python
# TODO: Implement multiple model types
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import tensorflow as tf

def train_position_models():
    """
    Train separate models for each position:
    1. XGBoost for tabular features (baseline)
    2. Random Forest for feature importance
    3. Neural Network for complex interactions
    4. LSTM for time series patterns
    """
    pass

def create_ensemble_model():
    """
    Combine multiple models:
    - Weight by recent performance
    - Use stacking/blending techniques
    - Cross-validation for robustness
    """
    pass

def implement_uncertainty_quantification():
    """
    Provide prediction confidence intervals:
    - Quantile regression
    - Monte Carlo dropout
    - Ensemble variance
    """
    pass
```

### Phase 3: Advanced Optimization

#### 3.1 Team Selection Optimization

```python
# TODO: Implement advanced optimization
from scipy.optimize import linprog
import pulp  # Linear programming

def implement_integer_programming():
    """
    Use mathematical optimization for team selection:
    - Exact solutions for budget/position constraints
    - Handle discrete choices (player selection)
    - Multi-objective optimization (points vs risk)
    """
    pass

def implement_genetic_algorithm():
    """
    Evolutionary algorithm for complex optimization:
    - Population of potential teams
    - Mutation and crossover operations
    - Handle multiple objectives simultaneously
    """
    pass

def implement_monte_carlo_simulation():
    """
    Risk analysis through simulation:
    - Generate thousands of possible outcomes
    - Measure team performance variance
    - Optimize for different risk profiles
    """
    pass
```

#### 3.2 Transfer Strategy Optimization

```python
# TODO: Multi-gameweek planning
def implement_lookahead_optimization():
    """
    Plan transfers for next 3-5 gameweeks:
    - Consider fixture difficulty sequences
    - Optimize transfer costs vs gains
    - Plan around price changes
    """
    pass

def implement_captaincy_optimization():
    """
    Advanced captain selection:
    - Separate model for captain multiplier
    - Consider opponent matchups
    - Risk/reward analysis for differential captains
    """
    pass
```

### Phase 4: Implementation Checklist

#### 4.1 Required Python Packages

```bash
# TODO: Install ML packages
pip install scikit-learn xgboost lightgbm tensorflow
pip install optuna  # Hyperparameter tuning
pip install pulp   # Linear programming
pip install plotly # Visualizations
pip install shap   # Model explanations
```

#### 4.2 Database Schema Extensions

```sql
-- TODO: Create additional tables for ML
CREATE TABLE historical_player_stats (
    player_id INT,
    gameweek_id INT,
    season VARCHAR(10),
    points INT,
    minutes INT,
    -- ... all FPL stats
);

CREATE TABLE feature_store (
    player_id INT,
    gameweek_id INT,
    rolling_avg_3gw DECIMAL,
    rolling_avg_5gw DECIMAL,
    form_trend DECIMAL,
    opponent_strength DECIMAL,
    -- ... engineered features
);

CREATE TABLE model_predictions (
    player_id INT,
    gameweek_id INT,
    predicted_points DECIMAL,
    confidence_lower DECIMAL,
    confidence_upper DECIMAL,
    model_version VARCHAR(50)
);
```

#### 4.3 File Structure for ML System

```
fpl-predictor/
├── ml/
│   ├── data_pipeline/
│   │   ├── feature_engineering.py
│   │   ├── data_collection.py
│   │   └── data_validation.py
│   ├── models/
│   │   ├── player_models.py
│   │   ├── ensemble_models.py
│   │   └── model_evaluation.py
│   ├── optimization/
│   │   ├── team_optimizer.py
│   │   ├── transfer_optimizer.py
│   │   └── captaincy_optimizer.py
│   └── utils/
│       ├── model_utils.py
│       └── evaluation_utils.py
├── trained_models/    # Saved model files
├── experiments/       # ML experiments and notebooks
└── config/           # ML configuration files
```

## 📊 Success Metrics & Validation

### Model Performance Targets

- **Prediction Accuracy**: Mean Absolute Error < 2.0 points
- **Hit Rate**: Top 3 predictions per position > 60% accuracy
- **Value Prediction**: Price change prediction > 70% accuracy
- **Team Performance**: Consistently rank in top 10% of FPL

### Validation Strategy

```python
# TODO: Implement validation framework
def time_series_cv():
    """
    Walk-forward validation:
    - Train on historical data
    - Test on future gameweeks
    - No data leakage from future
    """
    pass

def backtest_team_performance():
    """
    Historical team simulation:
    - Run AI on past seasons
    - Compare vs template teams
    - Measure long-term performance
    """
    pass
```

## 🚀 Quick Start Implementation Order

### Week 1: Data Foundation

1. ✅ Database is ready - start here
2. Implement historical data collection functions
3. Create basic feature engineering pipeline
4. Set up ML development environment

### Week 2: Baseline Models

1. Train simple XGBoost models per position
2. Implement basic evaluation metrics
3. Create prediction pipeline
4. Test on recent gameweeks

### Week 3: Advanced Features

1. Add rolling averages and form indicators
2. Implement ensemble models
3. Add uncertainty quantification
4. Optimize hyperparameters

### Week 4: Team Optimization

1. Implement mathematical optimization
2. Add multi-gameweek planning
3. Create transfer strategy logic
4. Build complete AI pipeline

## 💡 Key Implementation Notes

- **Start Simple**: Begin with XGBoost on basic features, then add complexity
- **Position-Specific**: Different models for GK/DEF/MID/FWD due to different scoring patterns
- **Time Awareness**: Always respect chronological order, no future leakage
- **Validation First**: Set up proper validation before optimizing models
- **Incremental**: Build each component separately, then integrate
- **Database Integration**: Leverage existing Supabase infrastructure

## 🎯 Next Action Items

1. **Immediate**: Set up `ml/` folder structure and install ML packages
2. **This Week**: Implement historical data collection from FPL API
3. **Next**: Create feature engineering pipeline using database data
4. **Goal**: Replace current rule-based system with trained ML models

Create a `.env` file in the project root:

```env
# Supabase Database Credentials
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# football-data.org API Key
API_KEY=your_football_data_api_key_here
```

**Getting Your Credentials:**

- **Supabase**: Sign up at [supabase.com](https://supabase.com), create a project, get URL and keys from Settings → API
- **football-data.org**: Register at [football-data.org](https://www.football-data.org/), get free API key (10 requests/minute)

### 5. Database Setup

The application will automatically create the required database schema on first run. Tables include:

- `teams` - Premier League team data
- `players` - Player information and mappings
- `gameweeks` - Season gameweek information
- `fixtures` - Match fixtures and results
- `current_player_stats` - Real-time player statistics
- `current_team_stats` - Team performance metrics
- `player_performances` - Historical performance data

## 🎮 Usage

### Running the Predictor

```bash
# Activate environment
env\Scripts\activate

# Run the predictor
python fpl-predictor.py
```

### First Run Setup

On the first run, the application will:

1. **Create team mappings** (instant - loads from database)
2. **Build player mappings** (~20 minutes due to API rate limits)
   - Maps 500+ players between FPL and football-data.org
   - Only needs to be done once, then cached in database
3. **Populate database** with current FPL data
4. **Generate predictions** and optimal team

### Subsequent Runs

After initial setup, the predictor runs in **seconds** using cached database data.

### Weekly Data Updates

Run this script to refresh data for new gameweeks:

```bash
python populate_db.py
```

## 📊 Output

The predictor generates:

### 🏆 Top Players by Position

```
TOP 3 FORWARDS:
  1. Erling Haaland - 8.2 pts (£15.1m, 45.2% owned)
  2. Alexander Isak - 7.1 pts (£8.5m, 12.8% owned)
  3. Darwin Núñez - 6.8 pts (£9.0m, 8.3% owned)
```

### 💰 Transfer Recommendations

- **Best Value Picks**: Highest points per million ratio
- **Highest Predicted Points**: Top point scorers regardless of price
- **Differential Picks**: Low ownership (<5%) high potential players

### 🏆 Optimal 15-Player Team

```
BUDGET: £99.2m / £100.0m (£0.8m remaining)
FORMATION: 3-4-3
PREDICTED POINTS: 67.8

STARTING XI (3-4-3):
  GK: • Alisson (Liverpool) - 5.2pts - £5.5m

  DEF: • Virgil van Dijk (Liverpool) - 6.1pts - £6.0m
       • William Saliba (Arsenal) - 5.8pts - £5.5m
       • Joško Gvardiol (Man City) - 5.5pts - £5.5m
```

## 🧠 AI Model Architecture

### Current Implementation (Rule-Based)

The current system uses sophisticated rule-based algorithms that analyze:

- **Player Form**: Recent performance trends and points per game
- **Fixture Difficulty**: Upcoming opponent strength analysis
- **Team Strength**: Overall team performance metrics
- **Value Analysis**: Points per million optimization
- **Risk Assessment**: Injury status, rotation risk, ownership levels

### Future AI Enhancement Roadmap

For implementing advanced machine learning models, the system is designed to support:

#### Phase 1: Data Preparation

- **Historical Data Collection**: 3-5 seasons of player/team performance
- **Feature Engineering**: Rolling averages, form indicators, contextual features
- **External Data**: Weather, referee history, fixture congestion

#### Phase 2: ML Models

- **Gradient Boosting** (XGBoost/LightGBM) for tabular prediction
- **Neural Networks** for complex pattern recognition
- **Time Series Models** (LSTM/GRU) for sequential performance
- **Ensemble Methods** for robust predictions

#### Phase 3: Optimization

- **Multi-Objective Optimization** for balanced risk/reward
- **Constraint Satisfaction** for FPL rule compliance
- **Transfer Strategy** for long-term team planning

## 📁 Project Structure

```
fpl-predictor/
├── fpl-predictor.py       # Main application
├── populate_db.py         # Data refresh script
├── .env                   # Environment variables
├── env/                   # Virtual environment
├── cache/                 # Legacy JSON cache (optional backup)
└── README.md             # This file
```

## 🔧 Configuration

### Key Settings

- **Budget**: Default £100m (modify in `build_optimal_team()`)
- **Player Mapping Threshold**: 200+ players for instant loading
- **API Rate Limits**: 6.5 second delays for football-data.org
- **Formation Options**: 7 different formations tested for optimal points

### Performance Optimization

- **Database First**: All data cached for instant access
- **Efficient Queries**: Optimized database lookups
- **API Minimization**: Reduce external API calls where possible

## 🚨 Troubleshooting

### Common Issues

**1. Slow Performance on First Run**

- Normal! Player mapping takes ~20 minutes due to API rate limits
- This only happens once - subsequent runs are instant

**2. Database Connection Errors**

- Check `.env` file has correct Supabase credentials
- Verify Supabase project is active and accessible

**3. API Key Errors**

- Ensure football-data.org API key is valid
- Free tier has 10 requests/minute limit

**4. Missing Player Mappings**

- Run `fpl-predictor.py` to rebuild mappings
- Check API connectivity and rate limits

### Environment Activation

If you see `'python' is not recognized` error:

```bash
# Windows
env\Scripts\activate
python fpl-predictor.py

# Or use full path
"C:\path\to\your\project\env\Scripts\python.exe" fpl-predictor.py
```

## 📈 Performance Metrics

- **Data Processing**: 743 players, 20 teams, 380+ fixtures
- **Prediction Speed**: <5 seconds for full team optimization
- **Database Size**: ~50MB for full season data
- **API Efficiency**: Minimal external calls after initial setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Fantasy Premier League API** - Official FPL data source
- **football-data.org** - Comprehensive football statistics
- **Supabase** - Database infrastructure
- **FPL Community** - Inspiration and feedback

## 📞 Support

For questions or issues:

1. Check the [troubleshooting section](#-troubleshooting)
2. Open an issue on GitHub
3. Join the discussion in issues section

---

**⚡ Quick Start:**

```bash
git clone https://github.com/ritvikiscool9/fpl-predictor.git
cd fpl-predictor
python -m venv env
env\Scripts\activate
pip install requests pandas python-dotenv supabase
# Add your .env file
python fpl-predictor.py
```

Happy FPL managing! 🏆⚽

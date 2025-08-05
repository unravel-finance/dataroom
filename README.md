# Unravel API Snippets

Simple Python snippets to get started with the Unravel API for portfolio backtesting and live weight retrieval.

## Purpose

This repository provides transparent, easy-to-understand code examples for:

- **Getting Started**: Quick setup and basic usage of the Unravel API
- **Backtest Validation**: Transparent backtesting code to validate portfolio performance
- **Live Weights**: Simple access to current portfolio allocations

## What's Included

### 📊 Portfolio Backtesting

- Transparent backtesting implementation with transaction costs
- Historical portfolio weights retrieval
- Performance visualization

### ⚡ Live Portfolio Data

- Real-time portfolio weight access
- Historical weight analysis
- Multi-portfolio support (beta.5, momentum_enhanced, etc.)

### 🔍 Factor Analysis

- Basic factor analysis using AlphaLens
- Portfolio factor historical data

## Installation

```bash
# Clone the repository
git clone https://github.com/unravel-finance/api-snippets.git
cd api-snippets

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export UNRAVEL_API_KEY="your_api_key_here"
```

### Dependencies

- `pandas`: Data manipulation
- `matplotlib`: Visualization
- `requests`: API calls
- `alphalens-reloaded`: Factor analysis
- `finml-utils`: Utilities

## Quick Start

### 1. Portfolio Backtesting

Run the complete portfolio backtesting example:

```bash
notebook_replicate_portfolio_backtest.ipynb
```

This notebook demonstrates:

- Fetching historical portfolio weights
- Getting underlying asset prices
- Running backtests with transaction costs
- Plotting performance results

### 2. Live Portfolio Weights

Get current portfolio allocations:

```bash
notebook_get_live_weights.ipynb
```

### 3. Factor Analysis

Analyze portfolio factors:

```bash
notebook_analyse_portfolio_factors.ipynb
```

## Available Scripts

- `run_replicate_portfolio_backtest.py`: Complete portfolio backtesting example
- `run_get_live_weights.py`: Get current portfolio weights
- `run_analyse_portfolio_factors.py`: Basic factor analysis

## License

These snippets are licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

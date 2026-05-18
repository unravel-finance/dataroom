# Unravel API Snippets

Simple Python snippets to get started with the Unravel API for portfolio backtesting and live weight retrieval — and the data-room pipeline that powers the Unravel sales process.

## Purpose

This repository provides transparent, easy-to-understand code examples for:

- **Getting Started**: Quick setup and basic usage of the Unravel API
- **Backtest Validation**: Transparent backtesting code to validate portfolio performance
- **Live Weights**: Simple access to current portfolio allocations
- **Sales data-room**: Auto-generated CSVs of historical returns / raw factor data and two-page PDF factsheets for every single-factor portfolio (see `scripts/`, `data/`, `factsheets/`)

## What's Included

### 📊 Portfolio Backtesting

- **`replicate_portfolio_backtest.py`**
- Transparent backtesting implementation with transaction costs
- Historical portfolio weights retrieval
- Performance visualization

### ⚡ Live Portfolio Data

- **`get_live_weights.py`**: Real-time portfolio weight access for current allocations

### 🔍 Factor Analysis

- Basic factor analysis using AlphaLens
- Portfolio factor historical data
- **`factor_analysis_altair.py`**: Factor analysis for the Altair portfolio using AlphaLens
- **`factor_analysis_carry_enhanced.py`**: Factor analysis for the Carry Enhanced portfolio
- **`factor_analysis_retail_flow.py`**: Factor analysis for the Retail Flow portfolio
- **`factor_returns_correlation.py`**: Cross-sectional returns correlation analysis between multiple portfolios

### 🛠️ Utilities

- **`convert_to_notebooks.py`**: Script to convert all Python files to Jupyter notebooks
- **`analysis/`**: Utility modules for backtesting, plotting, price data, and factor analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/unravel-finance/api-snippets.git
cd api-snippets

# Install the unravel-client package
pip install unravel-client

# Install other dependencies
pip install -r requirements.txt

# Set up environment variables
export UNRAVEL_API_KEY="your_api_key_here"
```

### Getting Your API Key

1. Visit [Unravel Finance](https://unravel.finance) and sign up for an account
2. Navigate to your API settings to generate an API key
3. Set the environment variable as shown above, or create a `.env` file in the project root:

```bash
echo "UNRAVEL_API_KEY=your_api_key_here" > .env
```

### Dependencies

- `unravel-client`: Official Unravel API client package
- `pandas`: Data manipulation
- `matplotlib`: Visualization
- `requests`: API calls
- `alphalens-reloaded`: Factor analysis
- `finml-utils`: Utilities

## Quick Start

The Python scripts use the `unravel-client` package. Make sure to install the package before running the scripts.

### 2. Portfolio Backtesting

Run the complete portfolio backtesting example:

```bash

jupyter notebook replicate_portfolio_backtest.ipynb
```

This script demonstrates:

- Fetching historical portfolio weights
- Getting underlying asset prices
- Running backtests with transaction costs
- Plotting performance results

### 3. Live Portfolio Weights

Get current portfolio allocations:

```bash
jupyter notebook get_live_weights.ipynb
```

### 4. Factor Analysis

Analyze portfolio factors:

```bash
jupyter notebook factor_analysis_altair.ipynb
jupyter notebook factor_analysis_carry_enhanced.ipynb
jupyter notebook factor_analysis_retail_flow.ipynb
```

### 5. Factor Returns Correlation

Analyze correlations between portfolio returns:

```bash
jupyter notebook factor_returns_correlation.ipynb
```

## Sales Data-Room Pipeline

The `.github/workflows/generate-factsheets.yml` workflow refreshes the public artefacts used by Unravel's outbound sales pipeline. It requires the `UNRAVEL_API_KEY` repo secret and is delivered by trigger: a **weekly schedule** (and manual dispatch) opens a PR into `main` for a human to review and merge; pushes to the setup branch commit straight back for fast design iteration.

For every single-factor portfolio defined in the catalog (`scripts/factors_catalog.py`), the workflow produces:

- `data/portfolio-40-returns/<factor>.csv` — daily returns of the unconstrained Top-40 portfolio
- `data/raw-factors/<factor>.csv` — raw cross-sectional factor data (per ticker, per day)
- `factsheets/<factor>.pdf` — two-page tear sheet (narrative + performance on page 1, AlphaLens factor analysis on page 2)

The artefacts are referenced directly from the Unravel Alpha web app (`apps/alpha`) via the raw GitHub URLs — no separate hosting required.

### Running locally

```bash
export UNRAVEL_API_KEY=...
# Export CSVs only
python -m scripts.export_data                  # all factors
python -m scripts.export_data altair momentum  # specific factors

# Render the PDF factsheets (does its own data fetch)
python -m scripts.generate_factsheets supply_velocity
```

The PDF layout lives under `scripts/factsheet/` — `theme.py` holds brand styling, `page_one.py` and `page_two.py` build each page.

## Available Portfolios

For a complete list of available portfolios and their parameters, visit [Unravel Portfolios](https://unravel.finance/portfolios).

## License

These snippets are licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Metropol Credit Portfolio Stress Lab

A standalone research prototype for market-driven credit portfolio stress testing and early-warning analytics for bureau-enabled lenders.

## Scope

The project is designed to complement bureau and lender risk systems. It does **not** build a consumer credit score and does not use real consumer, bureau, lender, or Metropol data.

The intended analytical chain is:

```text
Licensed WRDS market / fundamentals data
        +
Synthetic or authorized anonymized lender portfolio data
        ↓
Market and sector stress signals
        ↓
PD migration, expected loss, concentration analysis, VaR / ES
        ↓
Research dashboard and executive-ready visualisation
```

## Folder structure

```text
metropol-credit-portfolio-stress-lab/
├── analytics/
│   └── 01_wrds_inventory.py
├── data/
│   ├── raw/          # ignored by Git: licensed WRDS extracts
│   ├── processed/    # ignored by Git: transformed data
│   └── outputs/      # ignored by Git: model outputs
├── dashboard/
├── docs/
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Local setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a local `.env` file by copying `.env.example` and set your WRDS username. Never commit `.env`, a WRDS password, `.pgpass`, or licensed extracts.

## First task: WRDS inventory

Run:

```powershell
python .\analytics\01_wrds_inventory.py
```

The output lists the WRDS libraries and tables your account can access. Use that exact information before drafting any extraction SQL.

## Data and licensing

WRDS/CRSP/Compustat data are licensed. Keep raw extracts private unless your institutional license explicitly permits redistribution. The public dashboard should show derived, approved, non-sensitive summaries only.

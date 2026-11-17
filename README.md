<p align="center">
  <strong>🚇 TRANSIT AI</strong><br>
  <em>Intelligent Public Transportation Demand Forecasting &amp; Optimization System</em>
</p>

---

## Overview

**TRANSIT AI** is an end-to-end intelligent transit analytics platform that ingests real **MTA NYC Subway** ridership data, trains three ML/DL models (Random Forest, XGBoost, LSTM), and serves an interactive React dashboard with demand forecasting, peak-hour analytics, station rankings, and transport capacity optimization recommendations.

Built as an **MCA AIML capstone project**, it demonstrates a production-grade architecture with a React + Tailwind frontend, Flask REST API backend, and a full machine-learning pipeline — no dummy data or fabricated metrics.

---

## Features

| Module | Highlights |
|---|---|
| **Data Pipeline** | Automated download from NYC Open Data SODA API, cleaning, aggregation, feature engineering (lags, rolling stats, demand quartiles) |
| **ML Models** | Random Forest (R² 0.918), XGBoost (R² 0.923), LSTM (R² 0.921) — evaluated on a time-based hold-out set |
| **Forecasting Engine** | Hourly, daily, peak-hour, and weekday-vs-weekend forecasts per station |
| **Optimization** | Vehicle requirement estimation, fleet allocation, capacity-scenario comparison |
| **Analytics** | Borough stats, station rankings, heatmaps, monthly & weekly trends |
| **Dashboard** | 9-page SaaS-quality React app with dark mode, responsive layout, real API data |

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18 · Vite 5 · Tailwind CSS · Recharts · Lucide React · React Router · Axios |
| **Backend** | Python 3.11 · Flask · Flask-CORS · REST APIs |
| **ML / DL** | Scikit-learn · XGBoost · PyTorch (LSTM) |
| **Data** | Pandas · NumPy · Matplotlib · Seaborn |
| **Database** | SQLite (dev) / PostgreSQL (prod-ready via SQLAlchemy) |
| **Model Storage** | Joblib (RF, XGBoost) · PyTorch `.pt` (LSTM) |

---

## Project Structure

```
transit-ai/
├── backend/
│   ├── app.py                     # Flask application factory
│   ├── config.py                  # Configuration (DB URL, paths)
│   ├── run_pipeline.py            # CLI pipeline runner
│   ├── requirements.txt
│   ├── database/
│   │   ├── db.py                  # SQLite helper (init, record, query)
│   │   └── models.py              # SQLAlchemy model definitions
│   ├── routes/
│   │   ├── dashboard_routes.py    # /api/dashboard/*
│   │   ├── analytics_routes.py    # /api/analytics/*
│   │   ├── prediction_routes.py   # /api/predict, /api/forecast, /api/models/*
│   │   ├── optimization_routes.py # /api/optimization/*
│   │   └── data_routes.py         # /api/datasets/*
│   ├── src/
│   │   ├── data/                  # download, preprocess, pipeline
│   │   ├── features/              # feature engineering
│   │   ├── models/                # train_models, predict, saved/
│   │   ├── analytics/             # analytics_engine
│   │   ├── forecasting/           # forecast_engine
│   │   └── optimization/          # optimizer, capacity_planner
│   └── data/
│       ├── raw/                   # Downloaded CSV
│       └── processed/             # Aggregated + featured CSV
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx               # React entry point
│       ├── App.jsx                # Router
│       ├── index.css
│       ├── context/ThemeContext.jsx
│       ├── hooks/useFetch.js
│       ├── services/api.js
│       ├── utils/formatters.js
│       ├── layouts/MainLayout.jsx
│       ├── components/common/     # StatCard, Card, Badge, etc.
│       └── pages/
│           ├── OverviewDashboard.jsx
│           ├── DemandForecasting.jsx
│           ├── PeakHourAnalytics.jsx
│           ├── StationAnalytics.jsx
│           ├── WeekdayWeekendAnalysis.jsx
│           ├── TransportOptimization.jsx
│           ├── ModelPerformance.jsx
│           ├── DataManagement.jsx
│           └── Settings.jsx
└── README.md
```

---

## Quick Start

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the full data + ML pipeline
python run_pipeline.py
# Or run individual steps:
#   python run_pipeline.py --download
#   python run_pipeline.py --preprocess
#   python run_pipeline.py --features
#   python run_pipeline.py --train

# Start the Flask API server
python run_pipeline.py --serve
# Or: python -m flask run --port 5000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server (proxies /api to Flask on port 5000)
npm run dev
```

Open **http://localhost:3000** in your browser.

### 3. Production Build

```bash
cd frontend
npm run build        # Outputs to frontend/dist/
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/summary` | Overview statistics |
| GET | `/api/dashboard/trends` | Monthly ridership trends |
| GET | `/api/dashboard/recent-activity` | Recent prediction log |
| GET | `/api/analytics/hourly` | Hourly ridership distribution |
| GET | `/api/analytics/weekly` | Weekly ridership distribution |
| GET | `/api/analytics/monthly` | Monthly ridership distribution |
| GET | `/api/analytics/stations` | Station rankings |
| GET | `/api/analytics/boroughs` | Borough-level stats |
| GET | `/api/analytics/peak` | Peak-hour analysis |
| GET | `/api/analytics/weekday-weekend` | Weekday vs weekend comparison |
| GET | `/api/analytics/heatmap` | 24×7 heatmap matrix |
| POST | `/api/predict` | Single-point demand prediction |
| POST | `/api/forecast` | Multi-hour forecast |
| POST | `/api/forecast/daily` | Multi-day forecast |
| POST | `/api/forecast/peaks` | Peak-hour forecast |
| GET | `/api/models/performance` | Model evaluation metrics |
| POST | `/api/optimization/recommend` | Capacity recommendation |
| POST | `/api/optimization/allocate` | Fleet allocation |
| POST | `/api/optimization/scenarios` | Capacity scenario comparison |
| GET | `/api/datasets` | Dataset metadata |
| GET | `/api/datasets/preview` | Dataset record preview |
| GET | `/api/datasets/stations` | Station list |

---

## ML Model Performance

| Model | MAE | RMSE | R² |
|-------|-----|------|----|
| Random Forest | 360.48 | 611.39 | 0.9179 |
| XGBoost | 350.35 | 592.96 | 0.9227 |
| LSTM | 381.13 | 597.93 | 0.9214 |

> All metrics from actual evaluation on a time-based train/test split of real MTA data (Jan–Jun 2024, 50,400 records across 13 station complexes).

---

## Dataset

**MTA Subway Hourly Ridership (2024)** — sourced from [NYC Open Data](https://data.ny.gov/resource/wujg-7c2s.json).

- 104,910 raw rows (multiple fare classes per station-hour)
- Aggregated to 52,455 unique station-hour records
- 50,400 records after feature engineering (lag burn-in removed)
- Covers 13 Manhattan / Brooklyn / Queens station complexes

---

## License

This project is developed as an academic capstone. All MTA ridership data is publicly available under the NYC Open Data Terms of Use.

---

<p align="center">
  Built with ❤️ for the MCA AIML Capstone<br>
  <strong>TRANSIT AI</strong> — Making public transit smarter, one prediction at a time.
</p>

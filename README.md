# ✈️ AeroFare — AI Flight Fare Intelligence & Telemetry

An end-to-end Machine Learning and Real-Time Market Telemetry web application that estimates Indian domestic flight ticket fares from historical booking data, compares them against live market quotes, and visualizes cross-airline and advance-booking trends[cite: 9, 10].

> **Academic Prototype Notice:** AeroFare's ML baseline model is trained on historical Indian domestic flight records (`Clean_Dataset.csv`). When the optional **Live Market Tracker** toggle is enabled, the system compares live market quotes against the historical ML estimate; when toggled **OFF**, it operates purely as a historical ML fare estimator[cite: 9, 10].

---

## 👥 Team K — Scholars Institute of Technology and Management

* **Project Window:** 16–20 November 2026 *(Development: 16–18 Nov | Presentations: 19–20 Nov)*[cite: 9, 10]
* **Mostafizur Rahman** *(Team Leader)* — Data Preprocessing, Random Forest ML Model, FastAPI Backend, Live Market Telemetry Integration & Deployment,Frontend UI/UX Architecture & Chart.js Visualizations,Frontend Styling, Responsive Layout & Interactive Controls[cite: 9, 10]
* **Mahammad Ashif** — Frontend UI/UX Architecture & Chart.js Visualizations[cite: 9, 10]
* **Mountain Brahma** — Frontend Styling, Responsive Layout & Interactive Controls[cite: 9, 10]
* **Ruhan e Farhad** — End-to-End Sample Testing & Quality Assurance[cite: 9, 10]
* 

---

## ✨ Key Features

### Core Machine Learning & API Engine

* **Historical ML Fare Estimator (`POST /predict`):** Predicts estimated flight fares in Indian Rupees (`₹`) using a trained `scikit-learn` **Random Forest Regressor** (`aerofare_model.joblib`) across 29 one-hot encoded features (`model_columns.joblib`), achieving a holdout test Mean Absolute Error (MAE) of **~₹1,084.95**.
* **Automated Lead-Time Calculation:** Dynamically computes `days_left` from the user's selected `travel_date` (`YYYY-MM-DD`) on the backend.

### Hybrid Live Telemetry & Interactive Frontend

* **Live Market Tracker ON/OFF Toggle (`POST /analyze`):** Switch seamlessly between **Hybrid Mode** (comparing real-time market lowest fares via `live_tracker.py` against the historical ML baseline with an AI Deal Verdict banner) and **ML-Only Mode** (`Live Market Tracker: OFF`)[cite: 10].
* **Role-Based Navigation & Admin Controls:** Single-row responsive navigation bar with role-based login—`Admin ML Settings` (FastAPI server URL configurator) remains hidden for guests and standard users until an Admin signs in.
* **Interactive Analytics (Chart.js):**
  * **Live Market vs. Historical ML** comparison bar chart[cite: 10].
  * **All-Airline Historical Comparison** bar chart across 6 domestic carriers (`AirAsia`, `SpiceJet`, `IndiGo`, `GO_FIRST`, `Air_India`, `Vistara`)[cite: 9, 10].
  * **45-Day Booking Window Trend** line chart (`1` to `45` days ahead)[cite: 9, 10].
* **User Experience Enhancements:** Aerial glassmorphism UI with Light/Dark mode toggle, 1–9 passenger group fare multiplier, recent query history chips, 12-language UI switcher, and Cloudflare Quick Tunnel (`cloudflared`) HTTPS support[cite: 9, 10].

---

## 🛠️ Tech Stack

* **Machine Learning:** Python 3, `scikit-learn` (`RandomForestRegressor`), `pandas`, `numpy`, `joblib`
* **Backend & Telemetry:** FastAPI, Uvicorn, Pydantic v2, `requests` (`app.py`, `live_tracker.py`)[cite: 9, 10]
* **Frontend:** HTML5, CSS3 (Glassmorphism & CSS Variables), Vanilla JavaScript (ES6+), Chart.js
* **Dataset:** [Kaggle — Flight Price Prediction Dataset](https://www.kaggle.com/datasets/shubhambathwal/flight-price-prediction) (`CC0: Public Domain`, target column: `price`)[cite: 9]

---

## 📂 Repository Structure

```text
AeroFare/
├── backend/
│   ├── app.py                  # FastAPI REST API server (/predict & /analyze)
│   ├── live_tracker.py         # Live flight market telemetry module
│   ├── aerofare_model.joblib   # Trained Random Forest Regressor model
│   ├── model_columns.joblib    # Saved 29 post-encoding feature column names
│   └── requirements.txt        # Python dependencies
├── ml/
│   └── aerofare_model.ipynb    # EDA, preprocessing, model training & holdout test MAE
├── frontend/
│   └── index.html              # Single-file interactive web dashboard
├── docs/
│   └── PRD_Group_K_AeroFare.docx # Project Requirements Document
├── .gitignore                  # Excludes .venv, __pycache__, *.csv, and api.txt
└── README.md
```

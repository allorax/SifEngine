# SIF Engine - Local Execution & Deployment Guide

This guide provides instructions for running the **SIF (Serious Injury or Fatality) Risk Engine** locally (Backend, Pipeline, and Frontend) as well as deploying the full stack to Railway and Vercel.

---

## 1. Prerequisites

- **Python**: 3.10+ (Virtual environment `.venv` recommended)
- **Node.js**: 18+ & **npm**
- **Git**

---

## 2. Local Setup & Execution

### A. Backend Setup (FastAPI)

1. **Activate the Virtual Environment**:
   ```bash
   source .venv/bin/activate
   ```
   *(If creating a fresh virtual environment: `python3 -m venv .venv && source .venv/bin/activate`)*

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Run the Analysis Pipeline** *(Initial Data Processing)*:
   To run the analysis pipeline with a specific record limit (e.g., 1,000 base version or 5,000):
   ```bash
   python run_analysis.py --limit 1000
   ```

4. **Start the FastAPI Backend Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The backend API will be live at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

---

### B. Frontend Setup (React / Vite)

1. **Navigate to the Frontend Directory**:
   ```bash
   cd frontend
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Start the Development Server**:
   ```bash
   npm run dev
   ```
   The frontend application will be accessible at `http://localhost:5173`.

---

### C. Running Tests

Ensure all 33+ unit tests pass:
```bash
export MPLBACKEND=Agg
pytest
```

---

## 3. Deployment Instructions

### A. Deploy Backend to Railway

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Deployment readiness"
   git push origin main
   ```

2. **Deploy on Railway**:
   - Log into [Railway.app](https://railway.app/).
   - Click **New Project** -> **Deploy from GitHub repo**.
   - Select this repository.
   - Railway will automatically detect the root `Dockerfile` and `railway.json`.
   - Once deployed, copy your generated public backend URL (e.g., `https://sifengine-production.up.railway.app`).

---

### B. Deploy Frontend to Vercel

1. **Deploy on Vercel**:
   - Log into [Vercel.com](https://vercel.com/).
   - Click **Add New** -> **Project** and import your GitHub repository.
   - Set the **Root Directory** to `frontend`.
   - **Framework Preset**: `Vite`.

2. **Configure Environment Variables**:
   Add the following environment variable in Vercel settings:
   - `VITE_API_BASE_URL`: `https://your-railway-backend-url.up.railway.app`

3. **Deploy**:
   Click **Deploy**. Vercel will build the SPA using `vercel.json` rewrite routing.

---

## 4. Key Endpoints Summary

- **Health Check**: `GET /health`
- **Dashboard Summary**: `GET /dashboard/summary`
- **Risk Overview**: `GET /dashboard/risk-overview`
- **Forecasts**: `GET /dashboard/forecasts`
- **Cluster Drilldown**: `GET /clusters/drilldown`

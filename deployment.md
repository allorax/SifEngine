# SIF Engine - End-to-End Deployment & Integration Guide

This document outlines the complete step-by-step procedures for deploying the **FastAPI Backend** and **React Vite Frontend**, connecting them seamlessly via cloud services (Railway & Vercel), and setting up appropriate environment variables and CORS headers.

---

## 1. System Architecture Overview

```
               +----------------------------------+
               |          Vercel Cloud            |
               |  React Vite Frontend App (SPA)   |
               +----------------------------------+
                                |
                   HTTPS API Request (JSON)
                                |
                                v
               +----------------------------------+
               |          Railway Cloud           |
               |  FastAPI Backend (Docker/Uvicorn) |
               |     + SQLite WAL Database       |
               +----------------------------------+
```

- **Frontend Platform**: Vercel (Static Site Host & CDN)
- **Backend Platform**: Railway (Containerized Docker Service)
- **Communication Protocol**: HTTPS REST API (`fetch` calls with JSON payloads)
- **Cross-Origin Configuration**: FastAPI `CORSMiddleware`

---

## 2. Step 1: Prepare Codebase for Production

### A. Dynamic API URL Setup in Frontend
The frontend uses [frontend/src/config.js](file:///home/obsidian/Documents/SIFBACKUPBACKENDV1/SIF%20%28copy%201%29/SifEngine/frontend/src/config.js) to resolve the backend API URL:
- In production, it reads `import.meta.env.VITE_API_BASE_URL`.
- If unset, it falls back to `http://localhost:8000`.

### B. CORS Configuration in Backend
FastAPI in `app/main.py` is configured with `CORSMiddleware` allowing request origins from Vercel deployments:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 3. Step 2: Deploy Backend to Railway

### Prerequisites:
- A GitHub repository containing the codebase.
- A free/pro account on [Railway.app](https://railway.app/).

### Execution Steps:
1. **Push Changes to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy readiness"
   git push origin main
   ```

2. **Create New Project in Railway**:
   - Log into your Railway dashboard.
   - Click **+ New Project** -> **Deploy from GitHub repo**.
   - Select your repository.

3. **Configure Service Settings**:
   - Railway will automatically detect the root `Dockerfile` and `railway.json`.
   - Under **Settings** -> **Networking**, click **Generate Domain** (e.g., `sifengine-backend.up.railway.app`).

4. **Verify Backend Deployment**:
   - Open your browser or run `curl`:
     ```bash
     curl https://sifengine-backend.up.railway.app/health
     ```
   - Expect response: `{"status": "ok", "version": "1.0.0"}`

---

## 4. Step 3: Deploy Frontend to Vercel & Connect to Backend

### Prerequisites:
- Your Railway backend public URL (e.g. `https://sifengine-backend.up.railway.app`).
- A free/pro account on [Vercel.com](https://vercel.com/).

### Execution Steps:
1. **Import Repository to Vercel**:
   - Log into Vercel dashboard -> Click **Add New** -> **Project**.
   - Select your GitHub repository.

2. **Configure Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend` (Click *Edit* and select the `frontend` folder)

3. **Add Environment Variable**:
   - Expand the **Environment Variables** section.
   - Add Key: `VITE_API_BASE_URL`
   - Add Value: `https://sifengine-backend.up.railway.app` *(Replace with your actual Railway URL without trailing slash)*

4. **Deploy**:
   - Click **Deploy**.
   - Vercel will build the frontend application. `frontend/vercel.json` ensures SPA client-side routing works cleanly without 404 errors on page refreshes.

---

## 5. Step 4: Verification & End-to-End Testing

Once both services are deployed:

1. **Access the Frontend App**:
   Open your Vercel URL (e.g., `https://sif-engine.vercel.app`).

2. **Verify Network Calls**:
   - Open Browser Developer Tools (`F12`) -> **Network** tab.
   - Select any window (Overview, Risk Matrix, Cluster 3D, Forecasts).
   - Ensure network requests go to `https://sifengine-backend.up.railway.app/...` and return HTTP `200 OK`.

3. **Check Console Log**:
   - Confirm no CORS errors (`Access-Control-Allow-Origin`) appear in the browser console.

---

## 6. Troubleshooting Common Issues

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **CORS Error in Console** | Backend blocking frontend origin domain | Update `allow_origins` in `app/main.py` to include your Vercel URL or `["*"]`. |
| **Mixed Content Warning** | Frontend (HTTPS) requesting Backend (HTTP) | Ensure `VITE_API_BASE_URL` starts with `https://`, not `http://`. |
| **Frontend 404 on Refresh** | SPA routing fallback missing | Confirm `frontend/vercel.json` exists with rewrite rule `"source": "/(.*)", "destination": "/index.html"`. |
| **Database Resets on Restart** | Ephemeral container filesystem | On Railway, attach a Persistent Volume to `/app/sif_engine.db` if persistent pipeline changes are needed. |

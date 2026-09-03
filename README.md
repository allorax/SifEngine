# SIH26165 OSHA Safety Incident & Hazard Pattern Analytics Engine

A fully working MVP backend system that processes OSHA safety incident reports through an end-to-end pipeline: data cleaning, NLP extraction, semantic embeddings, HDBSCAN clustering, risk scoring, trend analysis, and forecasting.

## Quick Start

### 1. Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python -m app.cli.init_db
```

### 3. Run Pipeline

**Small test (100 records):**
```bash
python -m app.cli.run_pipeline --limit 100
```

**Full dataset (106K+ records):**
```bash
python -m app.cli.run_pipeline
```

The pipeline will process OSHA data and output a JSON summary showing:
- Total records processed
- Number of clusters discovered
- Highest risk clusters with risk scores
- Increasing/emerging hazard patterns
- Trend classifications and forecasts

### 4. Start API Server

```bash
uvicorn app.main:app --reload
```

API documentation available at: http://localhost:8000/docs

### 5. Run Tests

```bash
pytest tests/ -v
```

## Architecture

### Data Pipeline

```
OSHA CSVs (2015-2025 comprehensive dataset + historical fatalities)
    ↓
Load & Parse (app/data/loader.py)
    ↓
Clean Data (app/data/cleaner.py)
    ↓
NLP Extraction (app/nlp/extractors.py)
    ↓
Generate Embeddings (app/ml/embeddings.py) - all-MiniLM-L6-v2
    ↓
HDBSCAN Clustering (app/ml/clustering.py)
    ↓
Cluster Labeling (app/ml/labeling.py)
    ↓
Risk Scoring (app/ml/risk.py) - 5-factor explainable score
    ↓
Trend Analysis (app/ml/trend.py) - classification + ratios
    ↓
Forecasting (app/ml/forecast.py) - exponential smoothing
    ↓
Database Storage (SQLite)
    ↓
FastAPI Endpoints
```

## Data Sources

The system processes OSHA incident reports from:

1. **Comprehensive Dataset (2015-2025)** - Primary data source
   - File: `data/osha/January2015toNovember2025.csv` (~106K records)
   - Fields: Employer, location, industry (NAICS), event type, narrative, severity indicators

2. **Historical Fatalities (2009-2012)** - Supplementary data
   - Files: `data/osha/FatalitiesFY*.csv`
   - All records are workplace fatalities

## Core Components

### Data Cleaning & Canonicalization

- Normalizes dates to ISO format (YYYY-MM-DD)
- Deduplicates records based on employer + date + description
- Validates presence of incident narratives
- Generates data profiling summary (counts, date range, industries, events)

### NLP Processing

Uses spaCy + predefined safety taxonomy to extract:
- **Hazard Categories**: Equipment Isolation/LOTO, Falls/Height, Electrical, Chemical, Confined Space, Struck-by, Lifting, Fire/Explosion, Pressure/Stored Energy, Loss of Containment
- **Equipment**: Forklift, scaffold, ladder, crane, conveyor, etc.
- **Activities**: Verb extraction from narratives
- **Unsafe Actions**: PPE issues, bypassed guards, etc.
- **Unsafe Conditions**: Structural failures, hazardous environments
- **Consequences**: Fatality, hospitalization, amputation, burns, etc.

### Embeddings

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional)
- Lightweight pretrained model suitable for laptop execution
- Normalized cosine similarity
- Batch processed (256 texts per batch)
- Stored as JSON in SQLite

### Clustering

- **Algorithm**: HDBSCAN with euclidean distance
- **Min Cluster Size**: 10 (configurable via `HDBSCAN_MIN_CLUSTER_SIZE`)
- **Min Samples**: 3 (configurable via `HDBSCAN_MIN_SAMPLES`)
- Discovers number of clusters automatically
- Handles noise points (cluster -1) gracefully

### Cluster Labeling

Evidence-based labeling from actual cluster content:
1. Primary: Dominant taxonomy hazard category
2. Secondary: Top equipment type
3. Tertiary: Top event classification
4. Fallback: Frequent keywords from narratives

### Risk Scoring

Explainable 0-100 risk score with 5 components:

- **Frequency** (25%): Cluster size relative to largest cluster
- **Near-Miss Intensity** (25%): Percentage of reports with precursor indicators
- **Severity** (20%): Fatality + hospitalization + amputation rates
- **Trend** (20%): Recent activity vs historical average
- **Recency** (10%): Percentage of reports in last 5 years

### Trend Analysis

Monthly time-series analysis classifying trends as:
- **Increasing**: Positive slope or recent avg > historical avg × 1.3
- **Decreasing**: Negative slope or recent avg < historical avg × 0.7
- **Emerging**: Low initial count with sudden jump in recent months
- **Fluctuating**: High standard deviation relative to mean
- **Stable**: Steady state

### Forecasting

Using statsmodels:
- **Holt's method** for clusters with ≥6 months of history (captures trend)
- **Simple exponential smoothing** for shorter histories
- **Linear regression fallback** if statsmodels fails
- 6-month forecast horizon
- Handles sparse data, zero counts, and constant series gracefully

## API Endpoints

All endpoints return JSON. CORS enabled for frontend integration.

### Health & Status
- `GET /health` - Service health check

### Reports
- `GET /reports` - List reports (paginated, filterable by state)
- `GET /reports/{id}` - Get single report
- `GET /reports/{id}/similar` - Find top N semantically similar reports

### Clusters
- `GET /clusters` - List all discovered clusters
- `GET /clusters/{id}` - Get cluster details
- `GET /clusters/{id}/reports` - Get reports in a cluster
- `GET /clusters/{id}/risk` - Get 5-factor risk score
- `GET /clusters/{id}/forecast` - Get trend + 6-month forecast

### Dashboard
- `GET /dashboard/summary` - Overview metrics for UI dashboard

### Pipeline
- `POST /pipeline/run` - Trigger full pipeline (optional `?limit=N` for subset)

## Database Schema

### Reports
- id, source_dataset, source_record_id, timestamp
- description, employer, location, state, industry
- event, source, severity_info (JSON)
- extracted_info (JSON), raw_data (JSON)
- embedding (JSON), cluster_id (FK)

### Clusters
- id, cluster_num, label, report_count, percentage
- dominant_event, dominant_hazard, dominant_industry, dominant_state
- min_date, max_date

### RiskScores
- id, cluster_id (FK), risk_score
- frequency, near_miss_intensity, severity, trend, recency

### Forecasts
- id, cluster_id (FK), trend_classification
- forecast_json (JSON array with monthly predictions)

## Test Coverage

**15 pytest tests** covering:
- Date normalization & parsing
- State abbreviation handling
- Company/address parsing
- Data cleaning & deduplication
- Vector serialization/deserialization
- Cosine similarity computation
- Cluster labeling from evidence
- Risk score calculation
- Trend classification
- Trend forecasting
- NLP safety info extraction
- API endpoints (health, reports, clusters, dashboard)

Run tests: `pytest tests/ -v`

## Configuration

Environment variables (optional):

```bash
DATABASE_PATH=/path/to/db.db           # Default: sif_engine.db in project root
EMBEDDING_MODEL=all-MiniLM-L6-v2       # Default: all-MiniLM-L6-v2
BATCH_SIZE=256                          # Default: 256 for embeddings
HDBSCAN_MIN_CLUSTER_SIZE=10            # Default: 10
HDBSCAN_MIN_SAMPLES=3                  # Default: 3
```

## Performance Notes

- **100 records**: ~15s (load + NLP + embeddings + clustering)
- **5,000 records**: ~60s (embeddings dominate)
- **106K records**: ~5-10 minutes (full comprehensive dataset)

Embedding generation is the computational bottleneck. The `all-MiniLM-L6-v2` model is optimized for CPU performance.

## Project Structure

```
sifEngine/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configuration
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # DB models
│   ├── schemas.py              # Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── reports.py
│   │   ├── clusters.py
│   │   ├── dashboard.py
│   │   └── pipeline.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py           # OSHA CSV loading
│   │   └── cleaner.py          # Data cleaning
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── taxonomy.py         # Safety taxonomy
│   │   └── extractors.py       # NLP extraction
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── embeddings.py       # SentenceTransformer
│   │   ├── clustering.py       # HDBSCAN
│   │   ├── labeling.py         # Cluster labels
│   │   ├── risk.py             # Risk scoring
│   │   ├── similarity.py       # Cosine similarity
│   │   ├── trend.py            # Trend analysis
│   │   └── forecast.py         # Time series forecasting
│   ├── services/
│   │   ├── __init__.py
│   │   └── pipeline.py         # End-to-end orchestration
│   └── cli/
│       ├── __init__.py
│       ├── init_db.py          # Database initialization
│       └── run_pipeline.py     # Pipeline CLI
├── tests/
│   ├── conftest.py
│   ├── test_loader.py
│   ├── test_cleaner.py (implied)
│   ├── test_nlp.py
│   ├── test_ml.py
│   └── test_api.py
├── data/
│   └── osha/                   # OSHA CSV files
├── requirements.txt
└── README.md
```

## Key Design Decisions

1. **SQLite Instead of PostgreSQL**: Sufficient for MVP, eliminates deployment complexity
2. **JSON Storage for Embeddings**: Simple, avoids pgvector dependency, embeddings loaded on-demand
3. **HDBSCAN Over K-Means**: Automatically discovers cluster count, handles outliers
4. **Pretrained Embeddings**: No training required, fast inference on CPU
5. **Lightweight Model**: `all-MiniLM-L6-v2` = 22MB, runs on any laptop
6. **Evidence-Based Labeling**: Uses actual cluster content, no ground truth assumptions
7. **Explainable Risk Score**: 5 factors make results interpretable
8. **Simple Forecasting**: Exponential smoothing handles most patterns, linear fallback

## Language & Terminology

The system identifies and forecasts **safety precursor patterns**, not accidents. Terms used:
- "Increasing hazard pattern" (not "accident will happen")
- "Emerging precursor cluster" (not "incident prediction")
- "Elevated risk trajectory" (not "risk of accident")
- "Forecasted increase in activity" (not "more accidents expected")

The system is designed to help identify where safety focus and intervention are needed, not to predict specific incidents.

## Limitations

1. **Encoding Issues in Older Datasets**: FY09-FY15 files have encoding problems; system gracefully skips them and prioritizes the comprehensive 2015-2025 dataset
2. **Text Quality**: Accuracy limited by quality of incident narratives in original OSHA data
3. **Taxonomy Static**: Safety hazard categories are fixed; adaptable but not dynamic
4. **No Real-time Updates**: Pipeline runs as batch process, not streaming
5. **English Only**: NLP tuned for English narratives
6. **Single GPU Unsupported**: Optimized for CPU, no CUDA acceleration
7. **No Authentication**: API has no auth; suitable for internal demos

## Future Enhancements

- Real-time pipeline with message queue
- Interactive cluster refinement UI
- Custom taxonomy per industry (NAICS code)
- Multi-language support
- Anomaly detection within clusters
- Root cause analysis using LLM
- Comparative analysis across industries/regions
- Export to dashboarding tools (Grafana, Tableau)

## Running for Demo

1. **Quick Demo (5min)**:
   ```bash
   python -m app.cli.init_db
   python -m app.cli.run_pipeline --limit 500
   uvicorn app.main:app --reload
   # Visit http://localhost:8000/docs
   # Try: GET /dashboard/summary, GET /clusters, GET /reports/1/similar
   ```

2. **Full Demo (10min)**:
   ```bash
   python -m app.cli.init_db
   python -m app.cli.run_pipeline --limit 5000
   uvicorn app.main:app --reload
   # Show dashboard, top risk clusters, increasing patterns
   ```

3. **Complete Dataset (10-15min)**:
   ```bash
   python -m app.cli.init_db
   python -m app.cli.run_pipeline
   # Full 106K records, comprehensive analysis
   ```

## Support & Troubleshooting

**Import errors**: Ensure you're using the virtual environment:
```bash
source .venv/bin/activate
```

**Embedding model not loading**: First run downloads ~22MB model. Requires internet:
```bash
pip install --upgrade sentence-transformers
```

**Database locked**: Close any other connections:
```bash
rm sif_engine.db
python -m app.cli.init_db
```

**Tests failing**: Use test database, not production:
```bash
pytest tests/ -v --tb=short
```

---

**Built for SIH26165 - OSHA Safety Incident & Hazard Pattern Analytics**

# OSHA Safety Analytics Pipeline - Master Controller

Complete end-to-end orchestration system for analyzing OSHA incident data with semantic clustering, risk assessment, and predictive analytics.

## Quick Start

```bash
# 100 records (fast test)
python run_analysis.py --limit 100

# 500 records (medium)
python run_analysis.py --limit 500

# 5000 records (large)
python run_analysis.py --limit 5000

# Full dataset (~115k records)
python run_analysis.py

# Skip visualizations (faster)
python run_analysis.py --limit 500 --no-plots

# Custom batch size
python run_analysis.py --batch-size 128
```

## Features

### Real-Time Progress Tracking
- Live stage completion indicators (✓, ⚙️, ✗)
- Detailed timing for each pipeline stage
- Performance metrics dashboard

### Comprehensive Analysis
- **Semantic Clustering**: HDBSCAN clustering on embeddings
- **Risk Assessment**: Multi-factor risk scoring (0-100)
- **Trend Prediction**: Emerging/Increasing/Stable/Decreasing trends
- **Forecast Analysis**: Statistical forecasting per cluster

### Embedding Optimization
- **Caching**: Reuses embeddings from previous runs (99% cache hit on second run)
- **Deduplication**: Single embedding for identical texts
- **Batching**: Efficient batch processing (configurable batch size)
- **CUDA Auto-Detection**: Uses GPU if available, falls back to CPU

### Visualizations (Optional)
- Cluster distribution chart
- Risk scores by cluster
- Temporal trends over time
- Embedding space PCA projection (2D)

## Output Structure

```
Pipeline runs produce:

1. Console Output
   ├─ Configuration summary
   ├─ Stage completion tracking
   ├─ Performance timing breakdown
   ├─ Database statistics
   ├─ Cluster analysis
   ├─ Risk assessment
   ├─ Trend predictions
   └─ Summary metrics

2. Database (SQLite)
   └─ sif_engine.db
      ├─ Reports (115k+ OSHA incidents)
      ├─ Clusters (semantic groups)
      ├─ Risk Scores (0-100 per cluster)
      └─ Forecasts (trend predictions)

3. Visualizations (if enabled)
   └─ output/plots/
      ├─ cluster_distribution.png
      ├─ risk_scores.png
      ├─ temporal_trends.png
      └─ embedding_clusters_pca.png
```

## Console Output Example

```
======================================================================
  OSHA Safety Analytics Pipeline
======================================================================

Configuration:
  Dataset: 500 records
  Batch Size: 64
  Visualizations: Enabled

✓  Database................................ SQLite initialized

──────────────────────────────────────────────────────────────────────
  Pipeline Execution
──────────────────────────────────────────────────────────────────────
[... processing ...]

──────────────────────────────────────────────────────────────────────
  Performance Metrics
──────────────────────────────────────────────────────────────────────

✓  Load.................................... 0.01s
✓  Clean................................... 0.00s
✓  Nlp..................................... 1.74s
✓  Embeddings.............................. 21.49s
✓  Clustering.............................. 0.00s
✓  Persistence............................. 0.00s
✓  Visualization........................... 0.00s

  Total Pipeline Time: 24.16s

──────────────────────────────────────────────────────────────────────
  Database Statistics
──────────────────────────────────────────────────────────────────────

  Total Reports: 500
  Reports with Embeddings: 500
  Clusters Discovered: 2
  Risk Scores: 2
  Forecasts: 2

──────────────────────────────────────────────────────────────────────
  Semantic Cluster Analysis
──────────────────────────────────────────────────────────────────────

  Found 2 semantic clusters:

  ┌─ Cluster 1: Falls / Working at Height
  │  Reports: 147 (29.4%)
  │  Risk Score: 71.2/100
  │  Trend: Stable
  │  Dominant Event: Fall on same level due to slipping
  │  Dominant Industry: 422110
  │  Dominant State: TX
  │  Date Range: 2015-01-01 to 2015-01-20
  └─

  ┌─ Cluster 2: Equipment Isolation / LOTO
  │  Reports: 73 (14.6%)
  │  Risk Score: 56.4/100
  │  Trend: Stable
  │  Dominant Event: Caught in running equipment or machinery during maintenance, cleaning
  │  Dominant Industry: 331111
  │  Dominant State: PA
  │  Date Range: 2015-01-01 to 2015-01-13
  └─

──────────────────────────────────────────────────────────────────────
  Risk Assessment
──────────────────────────────────────────────────────────────────────

  Risk Assessment (2 clusters):

  1. Falls / Working at Height
     Risk Score: 71.2/100 🟠 HIGH
     Frequency: 100.00
     Severity: 81.20
     Trend Factor: 50.00
     Recency Score: 0.00

  2. Equipment Isolation / LOTO
     Risk Score: 56.4/100 🟠 HIGH
     Frequency: 27.36
     Severity: 73.30
     Trend Factor: 50.00
     Recency Score: 0.00

──────────────────────────────────────────────────────────────────────
  Trend Predictions
──────────────────────────────────────────────────────────────────────

  Trend Predictions (2 clusters):

  →  Falls / Working at Height
     Trend: Stable
     Forecast Points: 20
     Avg Forecast Value: 7.35

  →  Equipment Isolation / LOTO
     Trend: Stable
     Forecast Points: 13
     Avg Forecast Value: 5.62

======================================================================
  Pipeline Complete
======================================================================

✓ Pipeline executed successfully

  Records processed: 500
  Clusters discovered: 2
  Total time: 24.16s

  Top Risk Clusters:
    • Falls / Working at Height: risk=71.2, reports=147
    • Equipment Isolation / LOTO: risk=56.4, reports=73

  Embedding Cache Hit Ratio: 99.8%
```

## Risk Score Interpretation

### Risk Level Indicators
- 🔴 **CRITICAL** (75-100): Immediate attention required
- 🟠 **HIGH** (50-74): Close monitoring needed
- 🟡 **MODERATE** (25-49): Standard precautions
- 🟢 **LOW** (0-24): Minimal risk

### Risk Factors
- **Frequency**: How often incidents occur
- **Severity**: Average injury severity per incident
- **Trend**: Direction of change (increasing/stable/decreasing)
- **Recency**: Weight on recent incidents
- **Near-Miss Intensity**: Potential for serious injury

## Trend Classifications

- **Emerging** (📈): New pattern, previously unseen
- **Increasing** (⬆️): Rising trend in recent data
- **Stable** (→): Consistent baseline
- **Decreasing** (⬇️): Declining trend
- **Fluctuating** (〰️): Erratic pattern

## Performance Benchmarks

| Dataset | Time | Clusters | Cache Hit |
|---------|------|----------|-----------|
| 100 records | ~13s | 2 | 99% |
| 500 records | ~24s | 2 | 99.8% |
| 5000 records | ~67s | 6 | 12% |
| 115k records | ~5-10min | 8-12 | Varies |

**Note**: Second run of same dataset is much faster due to embedding caching.

## Clustering Algorithm

**HDBSCAN** with:
- L2-normalized embeddings (semantic space)
- Euclidean metric (on normalized vectors ≈ cosine similarity)
- Min cluster size: 5
- Min samples: 2

Produces meaningful semantic groups like:
- Falls / Working at Height
- Equipment Isolation / LOTO
- Confined Space Entry
- Pressure / Stored Energy
- Struck/Cut Injuries

## Database Schema

```
Reports
├─ id (primary key)
├─ description (incident narrative)
├─ embedding (384-dim JSON array)
├─ cluster_id (foreign key)
├─ timestamp
├─ employer, location, state, industry
├─ event, severity_info
└─ extracted_info (NLP results)

Clusters
├─ id (primary key)
├─ cluster_num (HDBSCAN label)
├─ label (semantic name)
├─ report_count
├─ dominant_event, hazard, industry, state
└─ date range

RiskScores
├─ cluster_id (unique)
├─ risk_score (0-100)
├─ frequency, severity, trend, recency
└─ near_miss_intensity

Forecasts
├─ cluster_id (unique)
├─ trend_classification
└─ forecast_json (statistical predictions)
```

## Configuration Options

```bash
# Control dataset size
--limit 100          # Process exactly 100 records
--limit 500          # Process exactly 500 records
--limit 5000         # Process exactly 5000 records
(omit for full ~115k)

# Tune embedding processing
--batch-size 64      # Default: 64 (good for CPU)
--batch-size 128     # Faster on GPU

# Skip optional features
--no-plots           # Skip visualization generation (faster)
```

## Environment Variables

```bash
# Override batch size globally
export BATCH_SIZE=128

# Override HDBSCAN parameters
export HDBSCAN_MIN_CLUSTER_SIZE=5
export HDBSCAN_MIN_SAMPLES=2

# Use different database
export DATABASE_PATH=/path/to/db.sqlite
```

## Typical Workflow

```bash
# 1. Quick test on 100 records
python run_analysis.py --limit 100

# 2. Analyze patterns on 500 records
python run_analysis.py --limit 500

# 3. Check clustering quality on 5000 records
python run_analysis.py --limit 5000

# 4. Full analysis (if CPU time available)
python run_analysis.py

# 5. Re-run same size - verify caching efficiency
python run_analysis.py --limit 500  # Should be much faster
```

## Troubleshooting

**Issue**: "No clusters found"
- Increase dataset size (try 500+ records)
- HDBSCAN needs sufficient data density
- Check that embeddings are being generated

**Issue**: Slow embedding generation
- First run is slow (needs to download model)
- Subsequent runs much faster due to caching
- Use `--no-plots` to skip visualization rendering
- Increase `--batch-size` if on GPU

**Issue**: Memory error with full dataset
- Use `--limit 5000` to test with smaller sample
- Full 115k may require 8GB+ RAM
- Matplotlib visualization can use significant memory

**Issue**: Matplotlib not found
- System continues without visualization
- Plots are optional; core analysis works
- Install with: `pip install matplotlib --break-system-packages`

## Files Generated

```
sifEngine/
├─ run_analysis.py              (THIS FILE - master controller)
├─ sif_engine.db               (SQLite database)
├─ output/
│  └─ plots/                   (Generated visualizations)
│     ├─ cluster_distribution.png
│     ├─ risk_scores.png
│     ├─ temporal_trends.png
│     └─ embedding_clusters_pca.png
└─ app/
   ├─ ml/
   │  ├─ embeddings_optimized.py  (Caching + dedup)
   │  ├─ visualization.py         (Plot generation)
   │  └─ clustering.py            (HDBSCAN)
   ├─ services/
   │  └─ pipeline.py              (Core pipeline)
   └─ cli/
      └─ run_pipeline.py          (Pipeline entry)
```

## API Integration

The pipeline integrates with FastAPI:

```bash
# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Get dashboard summary
curl http://localhost:8000/dashboard/summary

# Get all clusters
curl http://localhost:8000/clusters

# Get top similar reports for report #1
curl http://localhost:8000/reports/1/similar?top_n=5
```

## Key Metrics Explained

### Frequency (0-100)
- Percentage of cluster size vs total dataset
- Higher = more prevalent pattern

### Severity (0-100)  
- Average injury severity in cluster
- Based on hospitalized, amputations, etc.

### Trend (0-100)
- Change rate over recent time period
- 50 = stable, >50 = increasing, <50 = decreasing

### Recency (0-100)
- Weight given to recent incidents
- Older incidents weighted less

### Near-Miss Intensity (0-100)
- Potential for severe injury
- Based on incident characteristics

## Running Tests

```bash
# Run all tests including optimization tests
python -m pytest tests/ -v

# Run only optimization tests
python -m pytest tests/test_optimization.py -v

# Run specific test
python -m pytest tests/test_optimization.py::TestEmbeddingOptimization::test_deduplication_detection -v
```

## Summary

This master controller provides:

✅ **Full control** over dataset size and parameters  
✅ **Real-time progress** tracking during execution  
✅ **Comprehensive results** displayed in terminal  
✅ **Risk assessment** with visual indicators  
✅ **Trend predictions** for each cluster  
✅ **Performance metrics** for optimization  
✅ **Matplotlib visualizations** (optional)  
✅ **Embedding caching** for efficiency  
✅ **Semantic clustering** on OSHA data  

Use `python run_analysis.py --limit 500` to see it in action!

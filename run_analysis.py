#!/usr/bin/env python3
"""
Master OSHA Analytics Pipeline Controller

Complete end-to-end orchestration with:
- Full progress tracking and visualization
- Real-time statistics reporting
- Comprehensive result analysis
- Risk assessment and predictions
- Matplotlib diagnostics
- User control over dataset size and parameters
"""

import sys
import json
import time
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

import numpy as np
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_database
from app.models import Report, Cluster, RiskScore, Forecast
from app.services.pipeline import execute_pipeline


class ProgressTracker:
    """Track and display pipeline progress."""

    def __init__(self):
        self.stages = {
            "load": {"status": "pending", "time": 0},
            "clean": {"status": "pending", "time": 0},
            "nlp": {"status": "pending", "time": 0},
            "embeddings": {"status": "pending", "time": 0},
            "clustering": {"status": "pending", "time": 0},
            "risk": {"status": "pending", "time": 0},
            "trend": {"status": "pending", "time": 0},
            "forecast": {"status": "pending", "time": 0},
            "persistence": {"status": "pending", "time": 0},
            "visualization": {"status": "pending", "time": 0},
        }

    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def print_stage(self, stage: str, status: str, details: str = ""):
        """Print stage status."""
        status_symbol = {
            "pending": "⏳",
            "running": "⚙️ ",
            "complete": "✓",
            "error": "✗",
        }.get(status, "?")

        stage_display = stage.replace("_", " ").title()
        if details:
            print(f"{status_symbol}  {stage_display:.<40} {details}")
        else:
            print(f"{status_symbol}  {stage_display}")

    def print_section(self, title: str):
        """Print a section divider."""
        print(f"\n{'─' * 70}")
        print(f"  {title}")
        print(f"{'─' * 70}\n")


class ResultsAnalyzer:
    """Analyze and display pipeline results."""

    def __init__(self, db: Session):
        self.db = db

    def get_database_stats(self) -> Dict[str, Any]:
        """Retrieve current database statistics."""
        reports_total = self.db.query(Report).count()
        reports_with_embeddings = (
            self.db.query(Report).filter(Report.embedding.isnot(None)).count()
        )
        clusters = self.db.query(Cluster).filter(Cluster.cluster_num != -1).count()
        risk_scores = self.db.query(RiskScore).count()
        forecasts = self.db.query(Forecast).count()

        return {
            "total_reports": reports_total,
            "reports_with_embeddings": reports_with_embeddings,
            "clusters": clusters,
            "risk_scores": risk_scores,
            "forecasts": forecasts,
        }

    def display_cluster_analysis(self):
        """Display detailed cluster analysis."""
        clusters = (
            self.db.query(Cluster)
            .filter(Cluster.cluster_num != -1)
            .order_by(Cluster.report_count.desc())
            .all()
        )

        if not clusters:
            print("  No clusters found.\n")
            return

        print(f"  Found {len(clusters)} semantic clusters:\n")

        for idx, cluster in enumerate(clusters, 1):
            risk = (
                self.db.query(RiskScore)
                .filter(RiskScore.cluster_id == cluster.id)
                .first()
            )
            forecast = (
                self.db.query(Forecast)
                .filter(Forecast.cluster_id == cluster.id)
                .first()
            )

            print(f"  ┌─ Cluster {idx}: {cluster.label}")
            print(f"  │  Reports: {cluster.report_count:,} ({cluster.percentage:.1f}%)")
            print(f"  │  Risk Score: {risk.risk_score:.1f}/100" if risk else "  │  Risk Score: N/A")
            print(f"  │  Trend: {forecast.trend_classification}" if forecast else "  │  Trend: N/A")
            print(f"  │  Dominant Event: {cluster.dominant_event}")
            print(f"  │  Dominant Industry: {cluster.dominant_industry}")
            print(f"  │  Dominant State: {cluster.dominant_state}")
            print(f"  │  Date Range: {cluster.min_date} to {cluster.max_date}")
            print(f"  └─\n")

    def display_risk_analysis(self):
        """Display risk assessment."""
        risks = (
            self.db.query(Cluster, RiskScore)
            .join(RiskScore, Cluster.id == RiskScore.cluster_id)
            .filter(Cluster.cluster_num != -1)
            .order_by(RiskScore.risk_score.desc())
            .all()
        )

        if not risks:
            print("  No risk scores found.\n")
            return

        print(f"  Risk Assessment ({len(risks)} clusters):\n")

        for rank, (cluster, risk) in enumerate(risks[:10], 1):
            risk_level = (
                "🔴 CRITICAL"
                if risk.risk_score >= 75
                else "🟠 HIGH"
                if risk.risk_score >= 50
                else "🟡 MODERATE"
            )

            print(f"  {rank}. {cluster.label}")
            print(f"     Risk Score: {risk.risk_score:.1f}/100 {risk_level}")
            print(f"     Frequency: {risk.frequency:.2f}")
            print(f"     Severity: {risk.severity:.2f}")
            print(f"     Trend Factor: {risk.trend:.2f}")
            print(f"     Recency Score: {risk.recency:.2f}\n")

    def display_trend_analysis(self):
        """Display trend predictions."""
        forecasts = (
            self.db.query(Cluster, Forecast)
            .join(Forecast, Cluster.id == Forecast.cluster_id)
            .filter(Cluster.cluster_num != -1)
            .all()
        )

        if not forecasts:
            print("  No forecasts found.\n")
            return

        print(f"  Trend Predictions ({len(forecasts)} clusters):\n")

        for cluster, forecast in forecasts:
            trend_icon = {
                "Emerging": "📈",
                "Increasing": "⬆️ ",
                "Stable": "→",
                "Decreasing": "⬇️ ",
                "Fluctuating": "〰️ ",
            }.get(forecast.trend_classification, "?")

            print(f"  {trend_icon}  {cluster.label}")
            print(f"     Trend: {forecast.trend_classification}")

            try:
                forecast_data = json.loads(forecast.forecast_json)
                if forecast_data and isinstance(forecast_data, list):
                    print(f"     Forecast Points: {len(forecast_data)}")
                    if forecast_data:
                        counts = [f.get("count", f.get("forecast", 0)) for f in forecast_data if isinstance(f, dict)]
                        if counts:
                            avg_forecast = float(np.mean(counts))
                            print(f"     Avg Forecast Value: {avg_forecast:.2f}")
            except Exception:
                pass

            print()

    def display_embedding_stats(self, embedding_stats: Dict[str, Any]):
        """Display embedding optimization statistics."""
        print("  Embedding Optimization:\n")
        print(f"  Total Texts: {embedding_stats['total_texts']:,}")
        print(f"  Unique Texts: {embedding_stats['unique_texts']:,}")
        print(f"  Cached Embeddings: {embedding_stats['cached_embeddings']:,}")
        print(f"  New Embeddings: {embedding_stats['new_embeddings']:,}")
        print(f"  Deduplication Ratio: {embedding_stats['deduplication_ratio']:.1f}%")
        print(f"  Device: {embedding_stats['device']} ({embedding_stats['device_name']})")
        print(f"  Batch Size: {embedding_stats['batch_size']}")
        print(f"  Embedding Time: {embedding_stats['embedding_time_sec']:.2f}s\n")

    def generate_visualizations(self) -> Dict[str, Optional[str]]:
        """Generate all diagnostic plots."""
        try:
            from app.ml.visualization import generate_all_diagnostics

            plots = generate_all_diagnostics(self.db)
            return plots
        except Exception as e:
            print(f"  Warning: Could not generate visualizations: {e}\n")
            return {}


class MainController:
    """Master controller for OSHA analytics pipeline."""

    def __init__(self, limit: Optional[int] = None, batch_size: int = 64, generate_plots: bool = True):
        self.limit = limit
        self.batch_size = batch_size
        self.generate_plots = generate_plots
        self.tracker = ProgressTracker()
        self.db = None
        self.results = {}

    def setup(self):
        """Initialize database and session."""
        self.tracker.print_header("OSHA Safety Analytics Pipeline")
        print(f"Configuration:")
        print(f"  Dataset: {'Full (115k records)' if self.limit is None else f'{self.limit:,} records'}")
        print(f"  Batch Size: {self.batch_size}")
        print(f"  Visualizations: {'Enabled' if self.generate_plots else 'Disabled'}\n")

        self.db = SessionLocal()
        init_database()
        self.tracker.print_stage("database", "complete", "SQLite initialized")

    def run_pipeline(self):
        """Execute the complete pipeline."""
        self.tracker.print_section("Pipeline Execution")

        start_time = time.perf_counter()

        try:
            self.results = execute_pipeline(
                self.db,
                limit=self.limit,
                generate_plots=self.generate_plots
            )

            if self.results["status"] != "success":
                self.tracker.print_stage("pipeline", "error", self.results.get("message", "Unknown error"))
                return False

            total_time = time.perf_counter() - start_time

            # Display timing breakdown
            self.tracker.print_section("Performance Metrics")
            timing = self.results.get("timing_breakdown", {})
            for stage, duration in timing.items():
                if stage != "total":
                    self.tracker.print_stage(stage, "complete", f"{duration:.2f}s")
            print(f"\n  Total Pipeline Time: {timing.get('total', total_time):.2f}s\n")

            return True

        except Exception as e:
            self.tracker.print_stage("pipeline", "error", str(e))
            import traceback
            traceback.print_exc()
            return False

    def analyze_results(self):
        """Analyze and display results."""
        if not self.results.get("status") == "success":
            print("Pipeline did not complete successfully. Skipping analysis.\n")
            return

        analyzer = ResultsAnalyzer(self.db)

        # Database stats
        self.tracker.print_section("Database Statistics")
        stats = analyzer.get_database_stats()
        print(f"  Total Reports: {stats['total_reports']:,}")
        print(f"  Reports with Embeddings: {stats['reports_with_embeddings']:,}")
        print(f"  Clusters Discovered: {stats['clusters']}")
        print(f"  Risk Scores: {stats['risk_scores']}")
        print(f"  Forecasts: {stats['forecasts']}\n")

        # Embedding stats
        if self.results.get("embedding_stats"):
            self.tracker.print_section("Embedding Optimization")
            analyzer.display_embedding_stats(self.results["embedding_stats"])

        # HDBSCAN results
        self.tracker.print_section("Clustering Results (HDBSCAN)")
        print(f"  Clusters Discovered: {self.results.get('clusters_discovered', 0)}")
        print(f"  Noise Ratio: {self.results.get('noise_percentage', 0):.1f}%\n")

        # Cluster analysis
        self.tracker.print_section("Semantic Cluster Analysis")
        analyzer.display_cluster_analysis()

        # Risk analysis
        self.tracker.print_section("Risk Assessment")
        analyzer.display_risk_analysis()

        # Trend analysis
        self.tracker.print_section("Trend Predictions")
        analyzer.display_trend_analysis()

        # Visualizations
        if self.generate_plots:
            self.tracker.print_section("Generated Visualizations")
            plots = analyzer.generate_visualizations()
            if plots:
                for plot_name, plot_path in plots.items():
                    if plot_path:
                        print(f"  ✓ {plot_name}: {plot_path}")
                    else:
                        print(f"  – {plot_name}: (skipped)")
            print()

    def display_summary(self):
        """Display final summary."""
        self.tracker.print_header("Pipeline Complete")

        if self.results.get("status") == "success":
            print(f"✓ Pipeline executed successfully\n")
            print(f"  Records processed: {self.results.get('total_records_processed', 0):,}")
            print(f"  Clusters discovered: {self.results.get('clusters_discovered', 0)}")
            print(f"  Total time: {self.results.get('processing_time_seconds', 0):.2f}s\n")

            if self.results.get("highest_risk_clusters"):
                print("  Top Risk Clusters:")
                for cluster in self.results["highest_risk_clusters"][:3]:
                    print(f"    • {cluster['label']}: risk={cluster['risk_score']:.1f}, reports={cluster['report_count']:,}")
                print()

            if self.results.get("embedding_stats"):
                stats = self.results["embedding_stats"]
                if stats["cached_embeddings"] > 0:
                    cache_ratio = (
                        stats["cached_embeddings"]
                        / (stats["cached_embeddings"] + stats["new_embeddings"])
                        * 100
                    )
                    print(f"  Embedding Cache Hit Ratio: {cache_ratio:.1f}%\n")

        else:
            print(f"✗ Pipeline failed: {self.results.get('message', 'Unknown error')}\n")

    def cleanup(self):
        """Clean up resources."""
        if self.db:
            try:
                self.db.commit()
                self.db.close()
            except Exception as e:
                print(f"Warning: Error during cleanup: {e}")

    def run(self) -> bool:
        """Execute complete analysis workflow."""
        try:
            self.setup()
            if not self.run_pipeline():
                return False

            self.analyze_results()
            self.display_summary()
            return True

        except KeyboardInterrupt:
            print("\n\n⚠️  Pipeline interrupted by user")
            return False
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="OSHA Safety Analytics Pipeline - Master Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py                    # Full dataset
  python run_analysis.py --limit 100        # 100 records
  python run_analysis.py --limit 500        # 500 records
  python run_analysis.py --limit 5000       # 5000 records
  python run_analysis.py --batch-size 128   # Custom batch size
  python run_analysis.py --no-plots         # Skip visualizations
        """
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Number of OSHA records to process (default: all ~115k)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Embedding batch size (default: 64)"
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip visualization generation"
    )

    args = parser.parse_args()

    # Create and run controller
    controller = MainController(
        limit=args.limit,
        batch_size=args.batch_size,
        generate_plots=not args.no_plots
    )

    success = controller.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

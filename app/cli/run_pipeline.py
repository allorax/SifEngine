"""CLI command to run the end-to-end OSHA processing pipeline."""
import argparse
import sys
import json
import matplotlib
matplotlib.use('Agg')
from app.database import SessionLocal
from app.services.pipeline import execute_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="Run SIH26165 OSHA Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli.run_pipeline                    # Full dataset
  python -m app.cli.run_pipeline --limit 100        # 100 reports
  python -m app.cli.run_pipeline --limit 500        # 500 reports
  python -m app.cli.run_pipeline --limit 5000       # 5000 reports
  python -m app.cli.run_pipeline --batch-size 128   # Custom batch size
  python -m app.cli.run_pipeline --sequential-limit # First records only
  python -m app.cli.run_pipeline --no-plots         # Skip visualizations
        """
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of OSHA records to process (None=full dataset)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for embedding generation (default: 64)"
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating diagnostic visualizations"
    )
    parser.add_argument(
        "--sequential-limit",
        action="store_true",
        help="Use the first records for --limit instead of a representative sample"
    )
    args = parser.parse_args()

    limit_str = f"with limit={args.limit:,}" if args.limit else "FULL DATASET"
    print(f"\n{'='*60}")
    print(f"OSHA Analytics Pipeline")
    print(f"{'='*60}")
    print(f"Mode: {limit_str}")
    print(f"Batch size: {args.batch_size}")
    print(f"Visualizations: {'Enabled' if not args.no_plots else 'Disabled'}")
    print(f"{'='*60}\n")

    db = SessionLocal()
    try:
        results = execute_pipeline(
            db,
            limit=args.limit,
            generate_plots=not args.no_plots,
            batch_size=args.batch_size,
            representative_sample=not args.sequential_limit,
        )

        # Print results summary
        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)

        if results["status"] == "success":
            print(f"\n✓ Status: SUCCESS")
            print(f"  Records processed: {results['total_records_processed']:,}")
            print(f"  Clusters discovered: {results['clusters_discovered']}")
            print(f"  Noise ratio: {results['noise_percentage']:.1f}%")
            print(f"  Total time: {results['processing_time_seconds']:.2f}s")

            if results.get('embedding_stats'):
                stats = results['embedding_stats']
                print(f"\n[Embedding Optimization]")
                print(f"  Unique texts: {stats['unique_texts']:,}")
                print(f"  Existing: {stats['existing_embeddings']:,}")
                print(f"  New required: {stats['new_embeddings_required']:,}")
                print(f"  Reused: {stats['reused_embeddings']:,}")
                print(f"  Dedup ratio: {stats['deduplication_ratio']:.1f}%")
                print(f"  Device: {stats['device']} ({stats.get('device_name', '')})")

            if results.get('plot_files'):
                print(f"\n[Generated Plots]")
                for plot_name, plot_path in results['plot_files'].items():
                    if plot_path:
                        print(f"  ✓ {plot_name}: {plot_path}")

            if results.get('highest_risk_clusters'):
                print(f"\n[Top Risk Clusters]")
                for cluster in results['highest_risk_clusters'][:3]:
                    print(f"  • {cluster['label']}: risk={cluster['risk_score']:.1f}, reports={cluster['report_count']:,}")

        else:
            print(f"\n✗ Status: FAILED")
            print(f"  Message: {results.get('message', 'Unknown error')}")

        print("\n" + "="*60 + "\n")

        # Explicit final commit
        db.commit()

    except Exception as e:
        print(f"✗ Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            db.close()
        except Exception as e:
            print(f"Error closing session: {e}")


if __name__ == "__main__":
    main()

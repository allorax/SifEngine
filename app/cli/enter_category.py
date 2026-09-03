"""CLI command to perform hierarchical drill-down into an OSHA category."""

import argparse
import sys
from app.database import SessionLocal
from app.services.category_drilldown import execute_category_drilldown


def main():
    parser = argparse.ArgumentParser(
        description="Hierarchical Subcategory Drill-down for OSHA Incident Categories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli.enter_category --category falls
  python -m app.cli.enter_category --category vehicle
  python -m app.cli.enter_category --category "electrical" --no-plots
  python -m app.cli.enter_category --category loto
        """
    )
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        help="Category name or keyword to drill down into (e.g. 'falls', 'vehicle', 'electrical')"
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating subcategory diagnostic visualizations"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for vector operations (default: 64)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for drill-down visualizations"
    )

    args = parser.parse_args()

    db = SessionLocal()
    try:
        results = execute_category_drilldown(
            db,
            category_input=args.category,
            generate_plots=not args.no_plots,
            output_dir=args.output_dir
        )

        if results["status"] == "category_not_found":
            print(f"\nCategory '{results['requested']}' not found.\n")
            print("Available categories:")
            for name, count in results["available"]:
                print(f"  • {name} ({count:,} reports)")
            print()
            sys.exit(1)

        if results["status"] == "error":
            print(f"\nError: {results['message']}\n")
            sys.exit(1)

        # Print formatted terminal output
        print("\n" + "=" * 60)
        print("OSHA CATEGORY DRILL-DOWN")
        print("=" * 60)
        print(f"Category: {results['category']}")
        print(f"Dataset scope: {results['total_dataset_records']:,} records")
        print(f"Records in category: {results['category_records']:,} ({results['category_percentage']}%)")
        print("=" * 60)

        print("\nSUBCATEGORIES DISCOVERED\n")
        for sub in results["subcategories"]:
            print(f"{sub['subcluster_num']}. {sub['label']}")
            print(f"   Reports: {sub['report_count']:,}")
            print(f"   Percentage: {sub['percentage']:.1f}%")
            print(f"   Risk Score: {sub['risk_score']:.1f}\n")

        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Subcategories discovered: {len(results['subcategories'])}")
        print(f"Records analysed: {results['category_records']:,}")
        print(f"Noise/unclassified: {results['noise_percentage']}%")
        print(f"Processing time: {results['processing_time']:.2f}s")

        if results.get("plot_files"):
            print("\nVisualizations saved:")
            for plot_name, plot_path in results["plot_files"].items():
                print(f"  ✓ {plot_name}: {plot_path}")

        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Error during category drill-down: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

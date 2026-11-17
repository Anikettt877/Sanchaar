#!/usr/bin/env python
"""
TRANSIT AI — Master Pipeline Runner

Usage (run from the backend/ directory):
    python run_pipeline.py                  # Run full pipeline
    python run_pipeline.py --download       # Download raw data only
    python run_pipeline.py --preprocess     # Preprocess raw data
    python run_pipeline.py --features       # Generate engineered features
    python run_pipeline.py --train          # Train ML models
    python run_pipeline.py --serve          # Start Flask API server

If no flags are given, --download --preprocess --features --train are all executed.
"""

import argparse
import sys
import os
import time

# Ensure the backend/ directory is importable and also the project root (for 'backend' package)
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)


def step_header(title: str):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {title}")
    print(f"{sep}\n")


def run_download():
    step_header("STEP 1 - Downloading MTA ridership data")
    from src.data.download_data import download_mta_data
    download_mta_data()


def run_preprocess():
    step_header("STEP 2 - Preprocessing & aggregation")
    from src.data.preprocess_data import preprocess_data
    preprocess_data()


def run_features():
    step_header("STEP 3 - Feature engineering")
    from src.features.feature_engineering import engineer_features
    engineer_features()


def run_train():
    step_header("STEP 4 - Training ML models")
    from src.models.train_models import main as train_main
    train_main()


def run_serve():
    step_header("STARTING Flask API server on port 5000")
    # Import the app as a package from project root
    from backend.app import create_app
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)


def main():
    parser = argparse.ArgumentParser(description="TRANSIT AI - Pipeline Runner")
    parser.add_argument("--download", action="store_true", help="Download raw data")
    parser.add_argument("--preprocess", action="store_true", help="Preprocess raw data")
    parser.add_argument("--features", action="store_true", help="Generate features")
    parser.add_argument("--train", action="store_true", help="Train ML models")
    parser.add_argument("--serve", action="store_true", help="Start Flask server")
    args = parser.parse_args()

    # If no specific flags, run full data pipeline
    any_flag = args.download or args.preprocess or args.features or args.train or args.serve
    if not any_flag:
        args.download = True
        args.preprocess = True
        args.features = True
        args.train = True

    start = time.time()

    if args.download:
        run_download()
    if args.preprocess:
        run_preprocess()
    if args.features:
        run_features()
    if args.train:
        run_train()

    if not args.serve:
        elapsed = time.time() - start
        print(f"\nPipeline completed in {elapsed:.1f}s")
    else:
        run_serve()


if __name__ == "__main__":
    main()

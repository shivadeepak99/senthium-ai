# Data Collection and Model Training Guide

This guide explains how to collect telemetry data and train custom ANN models for Senthium AI.

## Overview

The training pipeline consists of three main steps:

1. **Data Collection**: Use the DataLogger to collect labeled telemetry
2. **Feature Extraction**: Convert raw CSV data to ML-ready features
3. **Model Training**: Train the ANN predictor on your data

## Step 1: Data Collection

### Quick Start with Demo

Run the interactive data collection demo:

```bash
python demo_data_collection.py --mode interactive
```

Or run automated collection:

```bash
python demo_data_collection.py --mode automated
```

### Manual Data Collection

Use the DataLogger CLI directly:

```bash
# Example: Collect idle session for 60 seconds
python -m senthium_ai.monitors.data_logger \
    --session-id idle_session_1 \
    --task idle \
    --duration 60 \
    --interval 5 \
    --output data/raw

# Example: Collect download session
python -m senthium_ai.monitors.data_logger \
    --session-id download_session_1 \
    --task download \
    --time-remaining 10 \
    --user-present \
    --duration 120 \
    --output data/raw
```

### Task Types

Use these standard labels for consistency:

- `idle`: System is idle, no significant activity
- `download`: Downloading files or data
- `render`: Video/image rendering or media processing
- `training`: Machine learning model training
- `compile`: Building/compiling software
- `backup`: Backup operations or file transfers

### Recommended Data Collection

For good model performance, collect:

- **Minimum**: 20 sessions per task type (60+ total sessions)
- **Recommended**: 50+ sessions per task type (150+ total sessions)
- **Ideal**: 100+ sessions per task type (300+ total sessions)

Each session should be:
- At least 30 seconds (6+ samples at 5s interval)
- Representative of real usage patterns
- Properly labeled with task type

## Step 2: Feature Extraction

Convert raw CSV files to ML-ready features:

```bash
# Extract features from all CSVs in data/raw
python -m senthium_ai.utils.feature_extractor data/raw \
    --output data/processed/features.npz \
    --window-size 6 \
    --stride 1 \
    --normalize
```

## Step 3: Model Training

Train the ANN model on extracted features:

```bash
python train_model.py \
    --data data/processed/features.npz \
    --output models/custom_model.pkl \
    --epochs 100 \
    --learning-rate 0.01 \
    --hidden-size 16 \
    --normalize
```

## Step 4: Exploratory Data Analysis (Optional)

Use the Jupyter notebook for data analysis:

```bash
jupyter notebook notebooks/eda.ipynb
```

For complete documentation, see the full guide at: [docs/DATA_COLLECTION_GUIDE.md](docs/DATA_COLLECTION_GUIDE.md)

#!/usr/bin/env python3
"""
Model training script for Senthium AI ANN predictor.
Trains the neural network on collected telemetry data.
"""
import argparse
import logging
import numpy as np
from pathlib import Path
import pickle
from typing import Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error

import sys
sys.path.insert(0, str(Path(__file__).parent))

from senthium_ai.models import TaskPredictor
from senthium_ai.utils import FeatureExtractor

logger = logging.getLogger(__name__)


def load_data(data_source: str, window_size: int = 6, stride: int = 1) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load and extract features from data source.
    
    Args:
        data_source: Path to CSV file, NPZ file, or directory of CSV files
        window_size: Window size for feature extraction
        stride: Stride for sliding window
        
    Returns:
        Tuple of (X, y_class, y_time)
    """
    data_path = Path(data_source)
    
    # Check if NPZ file (pre-processed)
    if data_path.suffix == '.npz':
        logger.info(f"Loading pre-processed data from {data_source}")
        data = np.load(data_source)
        return data['X'], data['y_class'], data['y_time']
    
    # Otherwise extract from raw CSV
    logger.info(f"Extracting features from {data_source}")
    extractor = FeatureExtractor(window_size=window_size, stride=stride)
    
    if data_path.is_file():
        X, y_class, y_time = extractor.process_file(str(data_path))
    elif data_path.is_dir():
        X, y_class, y_time = extractor.process_directory(str(data_path))
    else:
        raise ValueError(f"{data_source} is not a valid file or directory")
    
    return X, y_class, y_time


def train_model(X_train: np.ndarray, y_train: np.ndarray,
                X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None,
                input_size: int = 25, hidden_size: int = 16, output_size: int = 3,
                epochs: int = 100, learning_rate: float = 0.01,
                early_stopping_patience: int = 10) -> TaskPredictor:
    """
    Train the ANN model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features (optional)
        y_val: Validation labels (optional)
        input_size: Number of input features
        hidden_size: Hidden layer size
        output_size: Number of output classes
        epochs: Maximum training epochs
        learning_rate: Learning rate
        early_stopping_patience: Epochs without improvement before stopping
        
    Returns:
        Trained TaskPredictor model
    """
    logger.info(f"Training model - input_size={input_size}, hidden_size={hidden_size}, epochs={epochs}")
    
    # Create model
    model = TaskPredictor(
        input_size=input_size,
        hidden_size=hidden_size,
        output_size=output_size
    )
    
    # Train with validation if provided
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(epochs):
        # Train on full batch
        losses = model.train(X_train, y_train, epochs=1, learning_rate=learning_rate)
        train_loss = losses[0]
        
        # Validate if validation set provided
        if X_val is not None and y_val is not None:
            # Compute validation loss
            val_predictions = [model.predict(x)[0] for x in X_val]
            val_loss = np.mean(val_predictions != y_val)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
            
            if patience_counter >= early_stopping_patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} - Train loss: {train_loss:.4f}, Val loss: {val_loss:.4f}")
        else:
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} - Train loss: {train_loss:.4f}")
    
    return model


def evaluate_model(model: TaskPredictor, X_test: np.ndarray, y_test: np.ndarray):
    """
    Evaluate model performance.
    
    Args:
        model: Trained TaskPredictor
        X_test: Test features
        y_test: Test labels
    """
    logger.info("Evaluating model on test set")
    
    # Get predictions
    predictions = []
    probabilities = []
    
    for x in X_test:
        pred, prob = model.predict(x)
        predictions.append(pred)
        probabilities.append(prob)
    
    predictions = np.array(predictions)
    probabilities = np.array(probabilities)
    
    # Classification metrics
    print("\n" + "="*60)
    print("Classification Report")
    print("="*60)
    print(classification_report(y_test, predictions, 
                               target_names=['idle', 'moderate', 'critical']))
    
    print("\n" + "="*60)
    print("Confusion Matrix")
    print("="*60)
    cm = confusion_matrix(y_test, predictions)
    print("              Predicted")
    print("              Idle  Moderate  Critical")
    for i, row_name in enumerate(['Idle', 'Moderate', 'Critical']):
        print(f"Actual {row_name:8s}  {cm[i][0]:4d}  {cm[i][1]:8d}  {cm[i][2]:8d}")
    
    # Accuracy
    accuracy = np.mean(predictions == y_test)
    print(f"\nOverall Accuracy: {accuracy:.2%}")
    
    # Per-class accuracy
    print("\nPer-Class Accuracy:")
    for i, class_name in enumerate(['idle', 'moderate', 'critical']):
        class_mask = y_test == i
        if np.sum(class_mask) > 0:
            class_acc = np.mean(predictions[class_mask] == y_test[class_mask])
            print(f"  {class_name}: {class_acc:.2%}")
    
    print("="*60 + "\n")


def save_model(model: TaskPredictor, output_path: str, 
               normalization_params: Optional[dict] = None):
    """
    Save trained model to file.
    
    Args:
        model: Trained TaskPredictor
        output_path: Path to save model
        normalization_params: Optional normalization parameters to save
    """
    output_path = Path(output_path)
    
    # Save model weights
    model_data = {
        'weights1': model.weights1,
        'bias1': model.bias1,
        'weights2': model.weights2,
        'bias2': model.bias2,
        'input_size': model.input_size,
        'hidden_size': model.hidden_size,
        'output_size': model.output_size
    }
    
    if normalization_params:
        model_data['normalization'] = normalization_params
    
    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    logger.info(f"Model saved to {output_path}")


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description='Train Senthium AI ANN Model')
    
    # Data arguments
    parser.add_argument('--data', '-d', required=True, help='Path to training data (CSV/NPZ/directory)')
    parser.add_argument('--output', '-o', default='models/ann_model.pkl', help='Output model file')
    
    # Feature extraction
    parser.add_argument('--window-size', '-w', type=int, default=6, help='Window size for features')
    parser.add_argument('--stride', '-s', type=int, default=1, help='Stride for sliding window')
    
    # Model architecture
    parser.add_argument('--hidden-size', type=int, default=16, help='Hidden layer size')
    
    # Training
    parser.add_argument('--epochs', '-e', type=int, default=100, help='Training epochs')
    parser.add_argument('--learning-rate', '-lr', type=float, default=0.01, help='Learning rate')
    parser.add_argument('--test-split', type=float, default=0.2, help='Test set split ratio')
    parser.add_argument('--val-split', type=float, default=0.1, help='Validation set split ratio')
    parser.add_argument('--random-seed', type=int, default=42, help='Random seed')
    
    # Options
    parser.add_argument('--normalize', '-n', action='store_true', help='Normalize features')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("Senthium AI - Model Training")
    print("="*60)
    print(f"Data source: {args.data}")
    print(f"Output model: {args.output}")
    print(f"Hidden size: {args.hidden_size}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning rate: {args.learning_rate}")
    print("="*60 + "\n")
    
    # Load data
    try:
        X, y_class, y_time = load_data(args.data, args.window_size, args.stride)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return 1
    
    if len(X) == 0:
        logger.error("No data loaded")
        return 1
    
    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
    logger.info(f"Class distribution: {np.bincount(y_class)}")
    
    # Normalize if requested
    normalization_params = None
    if args.normalize:
        from senthium_ai.utils import FeatureExtractor
        extractor = FeatureExtractor()
        X, mean, std = extractor.normalize_features(X)
        normalization_params = {'mean': mean, 'std': std}
        logger.info("Features normalized")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_class, test_size=args.test_split, random_state=args.random_seed,
        stratify=y_class
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=args.val_split / (1 - args.test_split),
        random_state=args.random_seed, stratify=y_train
    )
    
    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Train model
    try:
        model = train_model(
            X_train, y_train, X_val, y_val,
            input_size=X.shape[1],
            hidden_size=args.hidden_size,
            output_size=3,
            epochs=args.epochs,
            learning_rate=args.learning_rate
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return 1
    
    # Evaluate
    evaluate_model(model, X_test, y_test)
    
    # Save model
    try:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_model(model, args.output, normalization_params)
        print(f"✓ Model saved to {args.output}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        return 1
    
    print("\nTraining completed successfully!")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

"""
Artificial Neural Network model for predicting active/critical background tasks.
"""
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class TaskPredictor:
    """
    ANN-based predictor for identifying critical task activity.
    Uses a simple feed-forward neural network with backpropagation.
    """
    
    def __init__(self, input_size: int = 8, hidden_size: int = 16, output_size: int = 3):
        """
        Initialize the neural network.
        
        Args:
            input_size: Number of input features
            hidden_size: Number of hidden layer neurons
            output_size: Number of output classes (idle, moderate, critical)
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initialize weights with Xavier initialization
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))
        
        # Training history
        self.training_history = []
        
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def _sigmoid_derivative(self, x: np.ndarray) -> np.ndarray:
        """Derivative of sigmoid function."""
        return x * (1 - x)
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)
    
    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """Derivative of ReLU function."""
        return (x > 0).astype(float)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax activation function."""
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=1, keepdims=True)
    
    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Forward propagation.
        
        Args:
            X: Input features (batch_size, input_size)
            
        Returns:
            Tuple of (hidden layer output, final output, raw scores)
        """
        # Ensure X is 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)
            
        # Hidden layer
        z1 = np.dot(X, self.W1) + self.b1
        a1 = self._relu(z1)
        
        # Output layer
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = self._softmax(z2)
        
        return a1, a2, z2
    
    def predict(self, features: List[float]) -> Tuple[int, np.ndarray]:
        """
        Predict task criticality level.
        
        Args:
            features: Input feature vector
            
        Returns:
            Tuple of (predicted class, probability distribution)
            Classes: 0=idle, 1=moderate, 2=critical
        """
        X = np.array(features).reshape(1, -1)
        
        # Normalize features
        X_norm = self._normalize_features(X)
        
        _, output, _ = self.forward(X_norm)
        predicted_class = np.argmax(output[0])
        
        return predicted_class, output[0]
    
    def _normalize_features(self, X: np.ndarray) -> np.ndarray:
        """
        Normalize features to [0, 1] range.
        
        Args:
            X: Input features
            
        Returns:
            Normalized features
        """
        # Simple min-max normalization with expected ranges
        max_values = np.array([100, 100, 50, 10, 400, 100, 24, 200])  # Expected max values
        return np.clip(X / max_values, 0, 1)
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100, 
              learning_rate: float = 0.01) -> List[float]:
        """
        Train the neural network using backpropagation.
        
        Args:
            X: Training features (n_samples, input_size)
            y: Training labels (n_samples,) as class indices
            epochs: Number of training epochs
            learning_rate: Learning rate for gradient descent
            
        Returns:
            List of loss values per epoch
        """
        # Convert labels to one-hot encoding
        y_onehot = np.zeros((y.shape[0], self.output_size))
        y_onehot[np.arange(y.shape[0]), y] = 1
        
        losses = []
        
        for epoch in range(epochs):
            # Forward pass
            a1, a2, _ = self.forward(X)
            
            # Calculate loss (cross-entropy)
            loss = -np.mean(np.sum(y_onehot * np.log(a2 + 1e-8), axis=1))
            losses.append(loss)
            
            # Backward pass
            dz2 = a2 - y_onehot
            dW2 = np.dot(a1.T, dz2) / X.shape[0]
            db2 = np.sum(dz2, axis=0, keepdims=True) / X.shape[0]
            
            da1 = np.dot(dz2, self.W2.T)
            dz1 = da1 * self._relu_derivative(a1)
            dW1 = np.dot(X.T, dz1) / X.shape[0]
            db1 = np.sum(dz1, axis=0, keepdims=True) / X.shape[0]
            
            # Update weights
            self.W2 -= learning_rate * dW2
            self.b2 -= learning_rate * db2
            self.W1 -= learning_rate * dW1
            self.b1 -= learning_rate * db1
            
            if epoch % 10 == 0:
                logger.debug(f"Epoch {epoch}, Loss: {loss:.4f}")
        
        self.training_history.extend(losses)
        return losses
    
    def get_task_level(self, features: List[float]) -> str:
        """
        Get human-readable task level.
        
        Args:
            features: Input feature vector
            
        Returns:
            Task level as string: 'idle', 'moderate', or 'critical'
        """
        predicted_class, probabilities = self.predict(features)
        levels = ['idle', 'moderate', 'critical']
        return levels[predicted_class]

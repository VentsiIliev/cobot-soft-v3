#!/usr/bin/env python3
"""
Model Configuration Classes for Shape Matching Training

This module contains configuration classes for different machine learning models
used in the shape matching system, with comprehensive parameter documentation.
"""

from dataclasses import dataclass
from typing import Optional, Union, Literal
from sklearn.linear_model import SGDClassifier
from sklearn.calibration import CalibratedClassifierCV


@dataclass
class SGDClassifierConfig:
    """
    Configuration for SGDClassifier (Stochastic Gradient Descent Classifier)
    
    SGD is an online learning algorithm that updates model parameters for each training sample,
    making it suitable for large datasets and online/incremental learning scenarios.
    """
    
    # ===== Core Algorithm Parameters =====
    
    loss: str = 'log_loss'
    """
    Loss function to use during training:
    - 'hinge': Standard SVM loss (gives linear SVM)
    - 'log_loss': Logistic regression loss (gives probabilistic output)
    - 'modified_huber': Smooth loss that combines hinge and logistic (robust to outliers)
    - 'squared_hinge': Quadratically penalized hinge loss
    - 'perceptron': Linear loss used by the perceptron algorithm
    - 'squared_error': Ordinary least squares (for regression)
    - 'huber': Huber loss (for regression, robust to outliers)
    - 'epsilon_insensitive': Linear loss that ignores errors smaller than epsilon (for regression)
    - 'squared_epsilon_insensitive': Squared epsilon-insensitive loss (for regression)
    
    For binary classification with probability estimates, use 'log_loss' or 'modified_huber'.
    """
    
    penalty: Optional[str] = 'l2'
    """
    Regularization term:
    - 'l2': Ridge regression penalty (default, good for most cases)
    - 'l1': Lasso penalty (promotes sparsity, feature selection)
    - 'elasticnet': Combination of L1 and L2 (requires l1_ratio parameter)
    - None: No regularization
    
    L2 penalty helps prevent overfitting by penalizing large weights.
    """
    
    alpha: float = 0.0001
    """
    Regularization strength (constant that multiplies the regularization term):
    - Higher values = stronger regularization = simpler model
    - Lower values = weaker regularization = more complex model
    - Typical range: 1e-6 to 1e-1
    - Default 0.0001 works well for most normalized datasets
    """
    
    l1_ratio: float = 0.15
    """
    The ElasticNet mixing parameter (only used if penalty='elasticnet'):
    - 0.0 = pure L2 penalty
    - 1.0 = pure L1 penalty  
    - 0.15 = 15% L1, 85% L2 (balanced mix)
    - Values between 0 and 1
    """
    
    # ===== Learning Parameters =====
    
    fit_intercept: bool = True
    """
    Whether to calculate the intercept (bias term):
    - True: Fit intercept (recommended for most cases)
    - False: Assume data is already centered
    
    Usually keep True unless you've manually centered your data.
    """
    
    max_iter: int = 1000
    """
    Maximum number of passes over the training data (epochs):
    - Higher values = more training time but potentially better convergence
    - Lower values = faster training but may not converge
    - Default 1000 is usually sufficient for most datasets
    - Monitor convergence warnings to adjust
    """
    
    tol: Optional[float] = 1e-3
    """
    Tolerance for stopping criterion:
    - Algorithm stops when loss improvement < tol for n_iter_no_change consecutive iterations
    - None: No tolerance-based stopping
    - Smaller values = stricter convergence (more iterations)
    - Larger values = looser convergence (fewer iterations)
    """
    
    shuffle: bool = True
    """
    Whether to shuffle training data after each epoch:
    - True: Shuffle data (recommended for better convergence)
    - False: Keep original order
    
    Shuffling helps prevent the model from learning order-dependent patterns.
    """
    
    verbose: int = 0
    """
    Verbosity level:
    - 0: Silent
    - 1: Print progress messages
    - >1: More detailed progress information
    """
    
    epsilon: float = 0.1
    """
    Epsilon parameter for epsilon-insensitive loss functions:
    - Only used with 'epsilon_insensitive' and 'squared_epsilon_insensitive' losses
    - Defines the tube within which no penalty is associated with the loss
    - Larger values = wider tube = more tolerance for errors
    """
    
    # ===== Learning Rate and Optimization =====
    
    learning_rate: str = 'optimal'
    """
    Learning rate schedule:
    - 'constant': eta = eta0 (constant learning rate)
    - 'optimal': eta = 1.0 / (alpha * (t + t0)) where t0 is chosen by heuristic
    - 'invscaling': eta = eta0 / pow(t, power_t)
    - 'adaptive': eta = eta0 as long as loss decreases, otherwise eta = eta/5
    
    'optimal' is usually the best choice for most problems.
    """
    
    eta0: float = 0.0
    """
    Initial learning rate:
    - Used with 'constant', 'invscaling', or 'adaptive' learning rate schedules
    - For 'optimal', this is ignored and learning rate is set automatically
    - Typical values: 0.01 to 1.0
    - Higher values = faster learning but risk overshooting
    """
    
    power_t: float = 0.5
    """
    Exponent for inverse scaling learning rate:
    - Only used when learning_rate='invscaling'
    - Controls how quickly the learning rate decreases
    - Values between 0 and 1
    - 0.5 is a good default (square root decay)
    """
    
    # ===== Early Stopping =====
    
    early_stopping: bool = False
    """
    Whether to use early stopping to terminate training when validation score stops improving:
    - True: Monitor validation score and stop when it stops improving
    - False: Train for max_iter epochs regardless of validation performance
    
    Requires validation_fraction > 0 when True.
    """
    
    validation_fraction: float = 0.1
    """
    Fraction of training data to set aside as validation set for early stopping:
    - Only used when early_stopping=True
    - Value between 0 and 1
    - 0.1 = use 10% of training data for validation
    """
    
    n_iter_no_change: int = 5
    """
    Number of iterations with no improvement to wait before early stopping:
    - Only used when early_stopping=True or tol is not None
    - Higher values = more patient (wait longer before stopping)
    - Lower values = less patient (stop sooner)
    """
    
    # ===== Data Handling =====
    
    class_weight: Optional[Union[dict, str]] = None
    """
    Weights associated with classes:
    - None: All classes have weight 1
    - 'balanced': Weights inversely proportional to class frequencies
    - dict: Manual weights {class_label: weight}
    
    Use 'balanced' for imbalanced datasets to give minority classes more importance.
    """
    
    warm_start: bool = False
    """
    Whether to reuse the solution of the previous call to fit:
    - True: Continue training from previous state (incremental learning)
    - False: Start fresh each time fit() is called
    
    Useful for online learning or when adding more data incrementally.
    """
    
    average: Union[bool, int] = False
    """
    Whether to compute averaged SGD weights:
    - False: No averaging
    - True: Average over all iterations
    - int: Average over the last 'average' iterations
    
    Averaging can help reduce variance and improve generalization.
    """
    
    # ===== System Parameters =====
    
    random_state: Optional[int] = 42
    """
    Random seed for reproducibility:
    - int: Fixed seed for reproducible results
    - None: Random initialization each time
    
    Set to a fixed value (like 42) for reproducible experiments.
    """


@dataclass
class CalibratedClassifierConfig:
    """
    Configuration for CalibratedClassifierCV (Probability Calibration)
    
    Calibration improves the reliability of predicted probabilities by mapping
    the classifier's output to better-calibrated probability estimates.
    """
    
    method: str = 'sigmoid'
    """
    Calibration method:
    - 'sigmoid': Platt scaling (assumes sigmoid-shaped calibration curve)
    - 'isotonic': Isotonic regression (non-parametric, more flexible)
    
    'sigmoid' works well when you have limited calibration data and the relationship
    is roughly sigmoid. 'isotonic' is more flexible but needs more data.
    """
    
    cv: Union[int, str, None] = 3
    """
    Cross-validation strategy for calibration:
    - int: Number of folds for stratified k-fold CV
    - 'prefit': Assume base estimator is already fitted
    - None or 1: No cross-validation (use entire training set)
    
    Higher CV folds = more robust calibration but longer training time.
    3-5 folds is usually a good balance.
    """
    
    n_jobs: Optional[int] = None
    """
    Number of parallel jobs for cross-validation:
    - None: Use 1 processor
    - int: Number of processors to use
    - -1: Use all available processors
    
    Parallelization only helps with cv > 1.
    """
    
    ensemble: bool = True
    """
    Whether to use ensemble of calibrators:
    - True: Fit one calibrator per CV fold, average predictions (more robust)
    - False: Fit single calibrator on full training set (faster)
    
    Ensemble is more robust but slightly slower.
    """


@dataclass
class SGDCalibratedConfig:
    """
    Complete configuration for SGD Online (Calibrated) model combining
    SGDClassifier with CalibratedClassifierCV
    """
    
    sgd_config: SGDClassifierConfig = None
    """Configuration for the base SGD classifier"""
    
    calibration_config: CalibratedClassifierConfig = None
    """Configuration for probability calibration"""
    
    def __post_init__(self):
        """Initialize default configurations if not provided"""
        if self.sgd_config is None:
            self.sgd_config = SGDClassifierConfig()
        if self.calibration_config is None:
            self.calibration_config = CalibratedClassifierConfig()
    
    def create_model(self):
        """
        Create the configured SGD Online (Calibrated) model
        
        Returns:
            CalibratedClassifierCV: Configured model ready for training
        """
        # Create base SGD classifier with configuration
        sgd = SGDClassifier(
            loss=self.sgd_config.loss,
            penalty=self.sgd_config.penalty,
            alpha=self.sgd_config.alpha,
            l1_ratio=self.sgd_config.l1_ratio,
            fit_intercept=self.sgd_config.fit_intercept,
            max_iter=self.sgd_config.max_iter,
            tol=self.sgd_config.tol,
            shuffle=self.sgd_config.shuffle,
            verbose=self.sgd_config.verbose,
            epsilon=self.sgd_config.epsilon,
            learning_rate=self.sgd_config.learning_rate,
            eta0=self.sgd_config.eta0,
            power_t=self.sgd_config.power_t,
            early_stopping=self.sgd_config.early_stopping,
            validation_fraction=self.sgd_config.validation_fraction,
            n_iter_no_change=self.sgd_config.n_iter_no_change,
            class_weight=self.sgd_config.class_weight,
            warm_start=self.sgd_config.warm_start,
            average=self.sgd_config.average,
            random_state=self.sgd_config.random_state
        )
        
        # Wrap with calibration
        calibrated_model = CalibratedClassifierCV(
            estimator=sgd,
            method=self.calibration_config.method,
            cv=self.calibration_config.cv,
            n_jobs=self.calibration_config.n_jobs,
            ensemble=self.calibration_config.ensemble
        )
        
        return calibrated_model
    
    def get_model_info(self):
        """
        Get human-readable information about the configured model
        
        Returns:
            dict: Model configuration summary
        """
        return {
            'model_type': 'SGD Online (Calibrated)',
            'base_classifier': 'SGDClassifier',
            'calibration_method': self.calibration_config.method,
            'loss_function': self.sgd_config.loss,
            'regularization': self.sgd_config.penalty,
            'alpha': self.sgd_config.alpha,
            'max_iterations': self.sgd_config.max_iter,
            'cv_folds': self.calibration_config.cv,
            'random_state': self.sgd_config.random_state
        }


# ===== Predefined Configurations =====

def get_default_sgd_calibrated_config():
    """
    Get the default configuration used in the original training script
    
    Returns:
        SGDCalibratedConfig: Default configuration
    """
    return SGDCalibratedConfig(
        sgd_config=SGDClassifierConfig(
            loss='log_loss',
            random_state=42
        ),
        calibration_config=CalibratedClassifierConfig(
            method='sigmoid',
            cv=3
        )
    )


def get_robust_sgd_calibrated_config():
    """
    Get a more robust configuration for noisy data
    
    Returns:
        SGDCalibratedConfig: Robust configuration
    """
    return SGDCalibratedConfig(
        sgd_config=SGDClassifierConfig(
            loss='modified_huber',  # More robust to outliers
            penalty='elasticnet',   # Combines L1 and L2
            alpha=0.001,           # Slightly stronger regularization
            l1_ratio=0.2,          # 20% L1, 80% L2
            max_iter=2000,         # More iterations
            early_stopping=True,   # Stop early if not improving
            validation_fraction=0.1,
            class_weight='balanced', # Handle class imbalance
            random_state=42
        ),
        calibration_config=CalibratedClassifierConfig(
            method='isotonic',     # More flexible calibration
            cv=5                   # More robust cross-validation
        )
    )


def get_fast_sgd_calibrated_config():
    """
    Get a configuration optimized for speed
    
    Returns:
        SGDCalibratedConfig: Fast training configuration
    """
    return SGDCalibratedConfig(
        sgd_config=SGDClassifierConfig(
            loss='log_loss',
            alpha=0.01,           # Higher alpha for faster convergence
            max_iter=500,         # Fewer iterations
            tol=1e-2,            # Looser tolerance
            random_state=42
        ),
        calibration_config=CalibratedClassifierConfig(
            method='sigmoid',     # Faster than isotonic
            cv=3,                # Fewer CV folds
            ensemble=False       # Single calibrator instead of ensemble
        )
    )


# ===== Usage Example =====

if __name__ == "__main__":
    # Example usage of the configuration classes
    
    print("=== Default Configuration ===")
    default_config = get_default_sgd_calibrated_config()
    model = default_config.create_model()
    print(f"Model: {model}")
    print(f"Info: {default_config.get_model_info()}")
    
    print("\n=== Robust Configuration ===")
    robust_config = get_robust_sgd_calibrated_config()
    print(f"Info: {robust_config.get_model_info()}")
    
    print("\n=== Fast Configuration ===")
    fast_config = get_fast_sgd_calibrated_config()
    print(f"Info: {fast_config.get_model_info()}")
    
    print("\n=== Custom Configuration ===")
    # Example of creating custom configuration
    custom_config = SGDCalibratedConfig(
        sgd_config=SGDClassifierConfig(
            loss='modified_huber',
            alpha=0.0005,
            max_iter=1500
        ),
        calibration_config=CalibratedClassifierConfig(
            method='isotonic',
            cv=4
        )
    )
    print(f"Custom Info: {custom_config.get_model_info()}")
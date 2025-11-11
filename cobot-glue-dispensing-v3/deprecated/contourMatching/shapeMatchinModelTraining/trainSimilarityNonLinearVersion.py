import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Import data loading module
from dataLoader import get_or_generate_pairs, load_dataset_for_testing
from featuresExtraction import compute_features_parallel, compute_enhanced_features
# Import model management module
from modelManager import save_model
# Import model configuration
from modelConfig import get_default_sgd_calibrated_config, get_robust_sgd_calibrated_config, get_fast_sgd_calibrated_config
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
# Import visualization module
from visualization import visualize_training_results


# ======================================================
# 🤖 Non-Linear Model Training
# ======================================================



def train_nonlinear_models(pairs, labels):
    print(f"🔄 Computing enhanced features for {len(pairs):,} pairs using parallel processing...")
    
    # Use multiprocessing for feature computation (most expensive part)
    n_cores = min(mp.cpu_count(), 8)  # Limit to 8 cores max
    print(f"💻 Using {n_cores} CPU cores for parallel processing...")
    
    # Add progress tracking for feature computation

    total_pairs = len(pairs)
    batch_size = 1000  # Process in batches for progress updates
    X = []
    completed = 0
    
    print(f"📊 Processing {total_pairs:,} pairs in batches of {batch_size:,}...")
    
    for i in range(0, total_pairs, batch_size):
        batch_pairs = pairs[i:i+batch_size]
        batch_size_actual = len(batch_pairs)
        
        with ProcessPoolExecutor(max_workers=n_cores) as executor:
            # Submit batch for processing
            batch_results = list(executor.map(compute_features_parallel, batch_pairs))
            X.extend(batch_results)
            
        completed += batch_size_actual
        progress = (completed / total_pairs) * 100
        print(f"   📈 Progress: {completed:,}/{total_pairs:,} pairs processed ({progress:.1f}%)")
    
    print(f"✅ Feature computation complete! Generated {len(X[0])} features per pair")
    y = np.array(labels)

    print("🔄 Splitting data for training and testing...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    print(f"📊 Training set: {len(X_train):,} samples, Test set: {len(X_test):,} samples")

    # Train multiple models with focus on online learning and proper confidence calibration
    print("🔧 Creating model configurations...")
    
    # Create different model configurations using the config classes
    default_config = get_default_sgd_calibrated_config()
    robust_config = get_robust_sgd_calibrated_config()
    fast_config = get_fast_sgd_calibrated_config()
    
    models = {
        # "SGD Online (Default)": default_config.create_model(),
        # "SGD Online (Robust)": robust_config.create_model(),
        # "SGD Online (Fast)": fast_config.create_model(),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
    }
    
    # Print model configurations for reference
    print("\n📋 Model Configurations:")
    print(f"   • Default: {default_config.get_model_info()}")
    print(f"   • Robust: {robust_config.get_model_info()}")
    print(f"   • Fast: {fast_config.get_model_info()}")
    
    results = {}
    
    for name, model in models.items():
        print(f"🔄 Training {name}...")
        model.fit(X_train, y_train)
        
        print(f"🔄 Evaluating {name}...")
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        
        results[name] = {
            'model': model,
            'accuracy': acc,
            'predictions': preds,
            'test_data': (X_test, y_test)
        }
        
        print(f"✅ {name} complete - Accuracy: {acc:.3f}")
    
    # Find best model
    best_model_name = max(results.keys(), key=lambda k: results[k]['accuracy'])
    best_result = results[best_model_name]
    
    print(f"\n🏆 Best model: {best_model_name} (Accuracy: {best_result['accuracy']:.3f})")
    
    # Print detailed results for best model
    print(f"\nDetailed Classification Report for {best_model_name}:")
    print(classification_report(y_test, best_result['predictions'], target_names=["Different", "Same"]))
    
    return results, best_model_name


# ======================================================
# 🚀 Main Execution
# ======================================================

if __name__ == "__main__":
    # Configuration flags
    ENABLE_VISUALIZATIONS = True  # Set to False for faster training
    GENERATE_NEW_PAIRS = True  # Set to False to load existing pairs instead of generating new ones
    PAIRS_FILE = None  # Path to specific pairs file (None = use most recent)
    
    # Generate dataset (only needed if generating new pairs)
    dataset = None
    if GENERATE_NEW_PAIRS:
        dataset = load_dataset_for_testing(n_shapes=22,
                                           n_scales=6,  # Reduced for faster processing
                                           n_variants=6,
                                           n_noisy=6,
                                           include_hard_negatives=True)  # Enable robust training
    
    # Get training pairs (either generate new or load existing)
    pairs, labels = get_or_generate_pairs(dataset, 
                                          generate_new_pairs=GENERATE_NEW_PAIRS, 
                                          pairs_file=PAIRS_FILE)
    
    results, best_model_name = train_nonlinear_models(pairs, labels)
    
    # Save the best model with dataset information
    best_model = results[best_model_name]['model']
    best_accuracy = results[best_model_name]['accuracy']
    
    # Prepare dataset info for model metadata
    dataset_info = {
        'pairs_generated': GENERATE_NEW_PAIRS,
        'pairs_file': PAIRS_FILE if not GENERATE_NEW_PAIRS else 'newly_generated',
        'dataset_generation_params': {
            'n_shapes': 22,
            'n_scales': 6,
            'n_variants': 6,
            'n_noisy': 6,
            'include_hard_negatives': True
        },
        'total_training_pairs': len(pairs),
        'feature_extraction_version': '2.0'  # With Harris corners
    }
    
    model_filepath = save_model(best_model, best_model_name, best_accuracy, dataset_info=dataset_info)
    
    # Run visualization and testing
    if ENABLE_VISUALIZATIONS:
        visualize_training_results(results, best_model_name, best_model, dataset)
    else:
        print(f"\n🎉 Training completed! Best model: {best_model_name} - Set ENABLE_VISUALIZATIONS=True to see detailed analysis.")
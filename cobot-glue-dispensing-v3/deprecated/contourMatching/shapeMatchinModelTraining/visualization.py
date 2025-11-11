import numpy as np
import matplotlib.pyplot as plt
import random
from sklearn.metrics import confusion_matrix
from featuresExtraction import compute_enhanced_features

# ======================================================
# 📊 Visualization and Testing Functions
# ======================================================

def create_comparison_plot(results):
    """Create comparison plot of all models"""
    model_names = list(results.keys())
    accuracies = [results[name]['accuracy'] for name in model_names]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(model_names, accuracies, color=['skyblue', 'lightcoral', 'lightgreen'])
    plt.title('Model Performance Comparison', fontsize=16)
    plt.ylabel('Accuracy', fontsize=14)
    plt.ylim(0.9, 1.0)  # Focus on high accuracy range
    
    # Add accuracy values on bars
    for bar, acc in zip(bars, accuracies):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001, 
                f'{acc:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.show()

def create_enhanced_confusion_matrix(results, model_name):
    """Create enhanced confusion matrix for best model"""
    result = results[model_name]
    cm = confusion_matrix(result['test_data'][1], result['predictions'])
    
    plt.figure(figsize=(10, 8))
    plt.imshow(cm, cmap="Blues")
    plt.title(f"Confusion Matrix - {model_name}", fontsize=16)
    
    # Add axis labels with class names
    plt.xlabel("Predicted Label", fontsize=14)
    plt.ylabel("True Label", fontsize=14)
    plt.xticks([0, 1], ["Different", "Same"], fontsize=12)
    plt.yticks([0, 1], ["Different", "Same"], fontsize=12)
    
    plt.colorbar()
    
    # Add numbers, percentages and descriptive text in each cell
    labels = [["True Negatives\n(Correctly Different)", "False Positives\n(Wrong: Called Same)"],
              ["False Negatives\n(Wrong: Called Different)", "True Positives\n(Correctly Same)"]]
    
    total_samples = np.sum(cm)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            count = cm[i, j]
            percentage = (count / total_samples) * 100
            plt.text(j, i, f'{count:,}\n({percentage:.1f}%)\n{labels[i][j]}', 
                    ha='center', va='center', color='red', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.show()

def run_model_tests(best_model, dataset=None):
    """
    Run comprehensive tests on the best model
    
    Args:
        best_model: The trained model to test
        dataset: Original dataset (optional, required for detailed tests)
    """
    print("\n" + "="*60)
    print("🔍 TESTING BEST MODEL")
    print("="*60)
    
    # Only run detailed tests if we have the original dataset
    if dataset is not None:
        # Test 1: Self-similarity test
        print("\n1️⃣ Self-Similarity Test (should predict 'Same'):")
        test_samples = random.sample(dataset, 3)
        for i, sample in enumerate(test_samples):
            features = compute_enhanced_features(sample.contour, sample.contour)
            prob = best_model.predict_proba([features])[0]
            prediction = best_model.predict([features])[0]
            result = "✅ SAME" if prediction == 1 else "❌ DIFFERENT"
            print(f"   {sample.variant_name}: {result} (confidence: {max(prob):.2f})")
        
        # Test 2: Known similar pairs test
        print("\n2️⃣ Known Similar Pairs Test (same object_id):")
        grouped = {}
        for s in dataset:
            grouped.setdefault(s.object_id, []).append(s)
        
        test_count = 0
        for obj_id, samples in grouped.items():
            if len(samples) >= 2 and test_count < 5:
                a, b = random.sample(samples, 2)
                features = compute_enhanced_features(a.contour, b.contour)
                prob = best_model.predict_proba([features])[0]
                prediction = best_model.predict([features])[0]
                result = "✅ SAME" if prediction == 1 else "❌ DIFFERENT"
                print(f"   {a.variant_name} vs {b.variant_name}: {result} (confidence: {max(prob):.2f})")
                test_count += 1
        
        # Test 3: Known different pairs test
        print("\n3️⃣ Known Different Pairs Test (different object_id):")
        object_ids = list(grouped.keys())
        for i in range(min(5, len(object_ids))):
            for j in range(i+1, min(i+2, len(object_ids))):
                a = random.choice(grouped[object_ids[i]])
                b = random.choice(grouped[object_ids[j]])
                features = compute_enhanced_features(a.contour, b.contour)
                prob = best_model.predict_proba([features])[0]
                prediction = best_model.predict([features])[0]
                result = "✅ DIFFERENT" if prediction == 0 else "❌ SAME"
                print(f"   {a.variant_name} vs {b.variant_name}: {result} (confidence: {max(prob):.2f})")
    else:
        print("\n📝 Detailed testing skipped (dataset not available - pairs were loaded from file)")
        print("   To run detailed tests, set GENERATE_NEW_PAIRS=True")

def visualize_training_results(results, best_model_name, best_model, dataset=None):
    """
    Complete visualization and testing workflow
    
    Args:
        results: Dictionary of training results for all models
        best_model_name: Name of the best performing model
        best_model: The best trained model
        dataset: Original dataset (optional, for detailed testing)
    """
    print(f"\n🎯 Starting visualization and testing for best model: {best_model_name}")
    
    # Model comparison plot
    print("📊 Creating model comparison plot...")
    create_comparison_plot(results)
    
    # Best model confusion matrix
    print("📊 Creating confusion matrix...")
    create_enhanced_confusion_matrix(results, best_model_name)
    
    # Run comprehensive tests
    run_model_tests(best_model, dataset)
    
    print(f"\n🎉 Visualization and testing completed for: {best_model_name}")
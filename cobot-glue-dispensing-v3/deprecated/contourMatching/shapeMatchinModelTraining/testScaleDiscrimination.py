#!/usr/bin/env python3
"""
Dedicated test script for validating scale discrimination while preserving R/T invariance.
This addresses the critical requirement: same shapes with different scales must be DIFFERENT.
"""

import random
from datasetGeneration import generate_synthetic_dataset, generate_shape, SyntheticContour
from trainSimilarityNonLinearVersion import train_nonlinear_models, generate_balanced_pairs, predict_similarity, save_model
from featuresExtraction import compute_enhanced_features

def create_scale_test_dataset():
    """Create a focused dataset specifically for testing scale discrimination"""
    print("🎯 Creating scale discrimination test dataset...")
    
    test_shapes = ['circle', 'rectangle', 'triangle', 'hexagon']
    scales = [0.3, 0.6, 1.0, 1.4, 1.8]  # Clearly distinct scales
    
    dataset = []
    
    for shape in test_shapes:
        for scale_idx, scale in enumerate(scales):
            print(f"   Generating {shape} at scale {scale:.1f}x...")
            
            for variant in range(3):  # 3 rotation variants
                try:
                    base = generate_shape(shape, scale)
                    
                    # Apply rotation (should preserve SAME classification)
                    from datasetGeneration import rotate_contour, jitter_contour
                    rotated = rotate_contour(base, random.uniform(0, 360))
                    
                    # Add minimal noise (should preserve SAME classification)
                    noisy = jitter_contour(rotated, 0.1)
                    
                    dataset.append(SyntheticContour(
                        contour=noisy,
                        object_id=f"{shape}_scale{scale_idx}",  # Different scales = different object_id
                        shape_type=shape,
                        scale=scale,
                        variant_name=f"{shape}_s{scale:.1f}_v{variant}"
                    ))
                except Exception as e:
                    print(f"     ⚠️ Error generating {shape} at scale {scale}: {e}")
    
    print(f"✅ Test dataset created with {len(dataset)} samples")
    return dataset

def test_scale_discrimination(model, model_name):
    """Test scale discrimination capabilities"""
    print(f"\n🧪 Testing Scale Discrimination for {model_name}")
    print("="*60)
    
    # Create controlled test cases
    test_shapes = ['circle', 'rectangle', 'triangle']
    
    results = {
        'scale_discrimination': {'correct': 0, 'total': 0, 'errors': []},
        'rotation_invariance': {'correct': 0, 'total': 0, 'errors': []},
        'noise_tolerance': {'correct': 0, 'total': 0, 'errors': []}
    }
    
    for shape in test_shapes:
        print(f"\n🔍 Testing {shape}...")
        
        # Test 1: Scale Discrimination (different scales should be DIFFERENT)
        try:
            small = generate_shape(shape, 0.5)
            large = generate_shape(shape, 1.5)
            
            result, confidence, _ = predict_similarity(model, small, large)
            expected = "DIFFERENT"
            is_correct = (result == expected)
            
            results['scale_discrimination']['total'] += 1
            if is_correct:
                results['scale_discrimination']['correct'] += 1
                status = "✅"
            else:
                results['scale_discrimination']['errors'].append((shape, result, confidence))
                status = "❌"
            
            print(f"   Scale discrimination: {status} {result} (confidence: {confidence:.3f}) - Expected: {expected}")
            
        except Exception as e:
            print(f"   Scale discrimination: ⚠️ Error: {e}")
        
        # Test 2: Rotation Invariance (same scale, different rotation should be SAME)
        try:
            from datasetGeneration import rotate_contour
            base = generate_shape(shape, 1.0)
            rotated = rotate_contour(base, 45)  # 45 degree rotation
            
            result, confidence, _ = predict_similarity(model, base, rotated)
            expected = "SAME"
            is_correct = (result == expected)
            
            results['rotation_invariance']['total'] += 1
            if is_correct:
                results['rotation_invariance']['correct'] += 1
                status = "✅"
            else:
                results['rotation_invariance']['errors'].append((shape, result, confidence))
                status = "❌"
            
            print(f"   Rotation invariance: {status} {result} (confidence: {confidence:.3f}) - Expected: {expected}")
            
        except Exception as e:
            print(f"   Rotation invariance: ⚠️ Error: {e}")
        
        # Test 3: Noise Tolerance (same scale + noise should be SAME)
        try:
            from datasetGeneration import jitter_contour
            base = generate_shape(shape, 1.0)
            noisy = jitter_contour(base, 0.2)  # Add noise
            
            result, confidence, _ = predict_similarity(model, base, noisy)
            expected = "SAME"
            is_correct = (result == expected)
            
            results['noise_tolerance']['total'] += 1
            if is_correct:
                results['noise_tolerance']['correct'] += 1
                status = "✅"
            else:
                results['noise_tolerance']['errors'].append((shape, result, confidence))
                status = "❌"
            
            print(f"   Noise tolerance: {status} {result} (confidence: {confidence:.3f}) - Expected: {expected}")
            
        except Exception as e:
            print(f"   Noise tolerance: ⚠️ Error: {e}")
    
    return results

def test_confidence_calibration(models):
    """Test confidence calibration across different models"""
    print(f"\n📊 Testing Confidence Calibration")
    print("="*60)
    
    # Create test pair (clearly different shapes)
    try:
        circle = generate_shape('circle', 1.0)
        square = generate_shape('rectangle', 1.0)
        
        print("Testing confidence values for clearly different shapes (circle vs rectangle):")
        
        for name, model_data in models.items():
            model = model_data['model']
            try:
                result, confidence, _ = predict_similarity(model, circle, square)
                print(f"   {name:25}: {result:9} (confidence: {confidence:.3f})")
            except Exception as e:
                print(f"   {name:25}: ⚠️ Error: {e}")
        
        print("\nTesting confidence values for similar shapes (circle vs circle rotated):")
        from datasetGeneration import rotate_contour
        circle_rotated = rotate_contour(circle, 90)
        
        for name, model_data in models.items():
            model = model_data['model']
            try:
                result, confidence, _ = predict_similarity(model, circle, circle_rotated)
                print(f"   {name:25}: {result:9} (confidence: {confidence:.3f})")
            except Exception as e:
                print(f"   {name:25}: ⚠️ Error: {e}")
                
    except Exception as e:
        print(f"⚠️ Confidence calibration test failed: {e}")

def print_test_summary(all_results):
    """Print comprehensive test summary"""
    print(f"\n📋 COMPREHENSIVE TEST SUMMARY")
    print("="*80)
    
    for model_name, results in all_results.items():
        print(f"\n🔸 {model_name.upper()}")
        
        # Scale Discrimination (most important)
        scale_correct = results['scale_discrimination']['correct']
        scale_total = results['scale_discrimination']['total']
        scale_acc = (scale_correct / scale_total * 100) if scale_total > 0 else 0
        
        print(f"   Scale Discrimination: {scale_correct}/{scale_total} = {scale_acc:.1f}%")
        if results['scale_discrimination']['errors']:
            print("   Scale errors:", [f"{shape}({result}, {conf:.2f})" for shape, result, conf in results['scale_discrimination']['errors']])
        
        # Rotation Invariance
        rot_correct = results['rotation_invariance']['correct']
        rot_total = results['rotation_invariance']['total']
        rot_acc = (rot_correct / rot_total * 100) if rot_total > 0 else 0
        
        print(f"   Rotation Invariance: {rot_correct}/{rot_total} = {rot_acc:.1f}%")
        
        # Noise Tolerance
        noise_correct = results['noise_tolerance']['correct']
        noise_total = results['noise_tolerance']['total']
        noise_acc = (noise_correct / noise_total * 100) if noise_total > 0 else 0
        
        print(f"   Noise Tolerance: {noise_correct}/{noise_total} = {noise_acc:.1f}%")
        
        # Overall Score
        total_correct = scale_correct + rot_correct + noise_correct
        total_tests = scale_total + rot_total + noise_total
        overall = (total_correct / total_tests * 100) if total_tests > 0 else 0
        print(f"   Overall Score: {total_correct}/{total_tests} = {overall:.1f}%")

def main():
    print("🚀 Scale Discrimination & R/T Invariance Validation")
    print("="*80)
    
    # Generate focused test dataset
    dataset = create_scale_test_dataset()
    
    # Generate training pairs
    pairs, labels = generate_balanced_pairs(dataset)
    print(f"\n📊 Training on {len(pairs)} pairs...")
    
    # Train models with enhanced features
    models, best_model_name = train_nonlinear_models(pairs, labels)
    
    # Test each model
    all_results = {}
    
    for model_name, model_data in models.items():
        model = model_data['model']
        results = test_scale_discrimination(model, model_name)
        all_results[model_name] = results
    
    # Test confidence calibration
    test_confidence_calibration(models)
    
    # Print comprehensive summary
    print_test_summary(all_results)
    
    # Save the best model if it passes scale discrimination
    best_results = all_results[best_model_name]
    scale_success_rate = best_results['scale_discrimination']['correct'] / best_results['scale_discrimination']['total']
    
    if scale_success_rate >= 0.8:  # 80% success rate threshold
        print(f"\n✅ Best model ({best_model_name}) passes scale discrimination test!")
        model_filepath = save_model(models[best_model_name]['model'], f"{best_model_name}_ScaleTested", models[best_model_name]['accuracy'])
        print(f"📁 Scale-validated model saved: {model_filepath}")
    else:
        print(f"\n❌ Best model ({best_model_name}) fails scale discrimination test ({scale_success_rate:.1%} success rate)")
        print("🔧 Consider adjusting scale-sensitive features or training parameters")

if __name__ == "__main__":
    main()
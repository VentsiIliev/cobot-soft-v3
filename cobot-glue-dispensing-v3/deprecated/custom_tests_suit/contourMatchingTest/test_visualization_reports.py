"""
Visualization and Reporting Module for Contour Matching Tests

This module contains all visualization and reporting functions for the contour
matching test suite, including:
- Test result visualizations
- Model fit analysis
- Low confidence reporting
- Comprehensive test analysis
"""

import numpy as np
import os
import csv
import io
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix

from API.shared.Contour import Contour
from custom_tests_suit.contourMatchingTest.testShapeGenerator import (
    create_rectangle_contour,
    create_triangle_contour,
    create_pentagon_contour,
    create_hexagon_contour,
    create_cross_contour,
    create_star_contour,
    create_l_shape_advanced_contour,
    create_u_shape_advanced_contour,
    create_convex_blob_contour,
    create_concave_blob_contour,
    rotate_contour,
    translate_contour
)


def visualize_test_result_matplotlib(workpieces, new_contours, matched, title="Match Test",
                                     match_info=None):
    """Visualize the matching result using matplotlib with match confidence scores."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Set aspect ratio and limits
    ax.set_aspect('equal')
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 800)
    ax.invert_yaxis()  # Invert Y axis to match image coordinates

    # Draw all workpieces in blue
    for wp in workpieces:
        wp_contour = wp.get_main_contour().squeeze()
        if wp_contour.ndim == 1:
            wp_contour = wp_contour.reshape(-1, 2)

        poly = Polygon(wp_contour, fill=False, edgecolor='blue', linewidth=2, label='Original WP')
        ax.add_patch(poly)

        # Add workpiece ID label
        contour_obj = Contour(wp.get_main_contour())
        centroid = contour_obj.getCentroid()
        ax.text(centroid[0], centroid[1], f"WP-{wp.workpieceId}",
               color='blue', fontsize=10, ha='center', weight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

    # Draw new contours in red
    for i, cnt in enumerate(new_contours):
        cnt_points = cnt.squeeze()
        if cnt_points.ndim == 1:
            cnt_points = cnt_points.reshape(-1, 2)

        poly = Polygon(cnt_points, fill=False, edgecolor='red', linewidth=2,
                      linestyle='--', label='New Detected')
        ax.add_patch(poly)

        contour_obj = Contour(cnt)
        centroid = contour_obj.getCentroid()

        # Get matching confidence if available
        if match_info and i < len(match_info):
            result, confidence, match_id = match_info[i]
            label_text = f"New-{i}\n{result}\nConf: {confidence:.1%}"
            bbox_color = 'lightgreen' if result == "SAME" else 'lightcoral'
        else:
            label_text = f"New-{i}"
            bbox_color = 'lightyellow'

        ax.text(centroid[0], centroid[1] + 20, label_text,
               color='darkred', fontsize=9, ha='center', weight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor=bbox_color, alpha=0.8))

    # Draw matched workpieces in green (aligned position)
    for idx, wp in enumerate(matched):
        aligned_contour = wp.get_main_contour().squeeze()
        if aligned_contour.ndim == 1:
            aligned_contour = aligned_contour.reshape(-1, 2)

        poly = Polygon(aligned_contour, fill=False, edgecolor='green', linewidth=3,
                      alpha=0.7, label='Matched & Aligned')
        ax.add_patch(poly)

        # Add alignment success indicator
        contour_obj = Contour(wp.get_main_contour())
        centroid = contour_obj.getCentroid()
        ax.plot(centroid[0], centroid[1], 'g*', markersize=15, alpha=0.6)

    # Add legend (remove duplicates)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=11,
             framealpha=0.9, edgecolor='black')

    # Add title and info box
    ax.set_title(title, fontsize=16, weight='bold', pad=20)

    # Add info box with statistics
    info_text = f"Workpieces: {len(workpieces)}\nNew Contours: {len(new_contours)}\nMatched: {len(matched)}"
    ax.text(10, 30, info_text, fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax.set_xlabel('X (pixels)', fontsize=12)
    ax.set_ylabel('Y (pixels)', fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def generate_low_confidence_report(all_test_details, test_config, confidence_threshold=0.80):
    """
    Generate comprehensive report for tests with confidence below threshold.

    Args:
        all_test_details: List of test detail dictionaries from test_known_match_pair
        test_config: Test configuration dictionary
        confidence_threshold: Threshold below which tests are flagged (default: 0.80)

    Returns:
        tuple: (low_conf_tests, report_text, csv_content)
    """
    print(f"\n{'='*70}")
    print(f"ANALYZING LOW CONFIDENCE TESTS (Threshold: {confidence_threshold:.0%})")
    print(f"{'='*70}")

    # Filter tests with low confidence
    low_conf_tests = [
        test for test in all_test_details
        if test['ml_confidence'] < confidence_threshold
    ]

    if len(low_conf_tests) == 0:
        print(f"  No tests with confidence below {confidence_threshold:.0%}")
        return [], "All tests have confidence >= {:.0%}".format(confidence_threshold), ""

    print(f"  Found {len(low_conf_tests)} test(s) with confidence < {confidence_threshold:.0%}")
    print(f"  Total tests analyzed: {len(all_test_details)}")
    print(f"  Percentage flagged: {len(low_conf_tests)/len(all_test_details)*100:.1f}%")

    # Group by category
    by_category = {}
    for test in low_conf_tests:
        category = test['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(test)

    # Generate text report
    report_lines = []
    report_lines.append("="*100)
    report_lines.append(f"LOW CONFIDENCE TEST REPORT (Threshold: {confidence_threshold:.0%})")
    report_lines.append("="*100)
    report_lines.append(f"\nGenerated: {test_config['output_base_dir']}")
    report_lines.append(f"Total Tests: {len(all_test_details)}")
    report_lines.append(f"Low Confidence Tests: {len(low_conf_tests)} ({len(low_conf_tests)/len(all_test_details)*100:.1f}%)")
    report_lines.append("\n" + "="*100)
    report_lines.append("FLAGGED TESTS BY CATEGORY")
    report_lines.append("="*100 + "\n")

    for category, tests in by_category.items():
        report_lines.append(f"\n{'#'*70}")
        report_lines.append(f"# {category} ({len(tests)} tests)")
        report_lines.append(f"{'#'*70}\n")

        for i, test in enumerate(tests, 1):
            report_lines.append(f"{i}. {test['test_name']}")
            report_lines.append(f"   Confidence: {test['ml_confidence']:.1%}")
            report_lines.append(f"   ML Result: {test['ml_result']}")
            report_lines.append(f"   Expected: {test['expected_result']}")
            report_lines.append(f"   Test Passed: {'YES' if test['test_passed'] else 'NO'}")
            report_lines.append(f"   Workpiece: {test['workpiece_name']}")
            report_lines.append(f"   Test Shape: {test['test_shape_name']}")
            report_lines.append(f"   Rotation: {test['rotation']}°")
            report_lines.append(f"   Translation: {test['translation']}")

            # Highlight if prediction was wrong
            if not test['test_passed']:
                report_lines.append(f"   >>> INCORRECT PREDICTION <<<")

            report_lines.append("")

    # Add summary statistics
    report_lines.append("\n" + "="*100)
    report_lines.append("SUMMARY STATISTICS")
    report_lines.append("="*100 + "\n")

    # Calculate stats
    correct_low_conf = sum(1 for t in low_conf_tests if t['test_passed'])
    incorrect_low_conf = len(low_conf_tests) - correct_low_conf

    avg_conf = sum(t['ml_confidence'] for t in low_conf_tests) / len(low_conf_tests)
    min_conf = min(t['ml_confidence'] for t in low_conf_tests)
    max_conf = max(t['ml_confidence'] for t in low_conf_tests)

    report_lines.append(f"Low Confidence Tests: {len(low_conf_tests)}")
    report_lines.append(f"  Correct Predictions: {correct_low_conf} ({correct_low_conf/len(low_conf_tests)*100:.1f}%)")
    report_lines.append(f"  Incorrect Predictions: {incorrect_low_conf} ({incorrect_low_conf/len(low_conf_tests)*100:.1f}%)")
    report_lines.append(f"\nConfidence Range:")
    report_lines.append(f"  Average: {avg_conf:.1%}")
    report_lines.append(f"  Min: {min_conf:.1%}")
    report_lines.append(f"  Max: {max_conf:.1%}")
    report_lines.append(f"\nBy Category:")
    for category, tests in by_category.items():
        report_lines.append(f"  {category}: {len(tests)} tests")

    report_lines.append("\n" + "="*100)
    report_lines.append("RECOMMENDATIONS")
    report_lines.append("="*100 + "\n")
    report_lines.append("1. Review flagged test cases to identify patterns")
    report_lines.append("2. Consider adding similar examples to training data")
    report_lines.append("3. Analyze feature distributions for low-confidence cases")
    report_lines.append("4. Check if specific shape combinations consistently have low confidence")
    report_lines.append("5. Validate that test transformations are realistic")

    report_text = "\n".join(report_lines)

    # Generate CSV content
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)

    # CSV header
    csv_writer.writerow([
        'Test Name', 'Category', 'Workpiece Name', 'Test Shape Name',
        'ML Result', 'ML Confidence', 'Expected Result', 'Test Passed',
        'Rotation (deg)', 'Translation X', 'Translation Y'
    ])

    # CSV data
    for test in low_conf_tests:
        csv_writer.writerow([
            test['test_name'],
            test['category'],
            test['workpiece_name'],
            test['test_shape_name'],
            test['ml_result'],
            f"{test['ml_confidence']:.4f}",
            test['expected_result'],
            'YES' if test['test_passed'] else 'NO',
            test['rotation'],
            test['translation'][0],
            test['translation'][1]
        ])

    csv_content = csv_buffer.getvalue()

    # Save reports
    output_dir = test_config["output_base_dir"]
    os.makedirs(output_dir, exist_ok=True)

    # Save text report
    txt_path = os.path.join(output_dir, "low_confidence_report.txt")
    with open(txt_path, 'w') as f:
        f.write(report_text)
    print(f"  Saved text report: {txt_path}")

    # Save CSV report
    csv_path = os.path.join(output_dir, "low_confidence_tests.csv")
    with open(csv_path, 'w', newline='') as f:
        f.write(csv_content)
    print(f"  Saved CSV report: {csv_path}")

    # Print summary to console
    print(f"\n{'='*70}")
    print(f"LOW CONFIDENCE SUMMARY")
    print(f"{'='*70}")
    print(f"  Flagged Tests: {len(low_conf_tests)}/{len(all_test_details)}")
    print(f"  Correct: {correct_low_conf}, Incorrect: {incorrect_low_conf}")
    print(f"  Average Confidence: {avg_conf:.1%}")
    print(f"  Reports saved to: {output_dir}/")
    print(f"{'='*70}")

    return low_conf_tests, report_text, csv_content


def visualize_test_clusters_and_model(all_results, test_config):
    """
    Create comprehensive visualizations showing:
    1. Test results clustered by category
    2. Model performance metrics
    3. Confidence distribution
    4. Failure analysis
    """
    print(f"\n{'='*70}")
    print(f"GENERATING VISUALIZATIONS - Test Clusters & Model Performance")
    print(f"{'='*70}")

    # Prepare data
    test_categories = {
        'Known Match': [],
        'Known Different': [],
        'Multiple Matches': [],
        'Rotation Stress': [],
        'Same Shape Different Size': []
    }

    for test_name, result in all_results:
        if 'Known Match' in test_name:
            test_categories['Known Match'].append((test_name, result))
        elif 'Known Different' in test_name:
            test_categories['Known Different'].append((test_name, result))
        elif 'Multiple Matches' in test_name:
            test_categories['Multiple Matches'].append((test_name, result))
        elif 'Rotation Stress' in test_name:
            test_categories['Rotation Stress'].append((test_name, result))
        elif 'Same Shape Different Size' in test_name:
            test_categories['Same Shape Different Size'].append((test_name, result))

    # Create comprehensive visualization
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # ========================================================================
    # Plot 1: Test Results by Category (Top Left)
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, 0])

    categories = []
    pass_counts = []
    fail_counts = []

    for category, tests in test_categories.items():
        if tests:
            passed = sum(1 for _, result in tests if result)
            failed = len(tests) - passed
            categories.append(category)
            pass_counts.append(passed)
            fail_counts.append(failed)

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax1.bar(x - width/2, pass_counts, width, label='Passed', color='green', alpha=0.7)
    bars2 = ax1.bar(x + width/2, fail_counts, width, label='Failed', color='red', alpha=0.7)

    ax1.set_xlabel('Test Category', fontsize=10, weight='bold')
    ax1.set_ylabel('Count', fontsize=10, weight='bold')
    ax1.set_title('Test Results by Category', fontsize=12, weight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=8)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=8)

    # ========================================================================
    # Plot 2: Overall Pass/Fail Pie Chart (Top Middle)
    # ========================================================================
    ax2 = fig.add_subplot(gs[0, 1])

    total_passed = sum(1 for _, result in all_results if result)
    total_failed = len(all_results) - total_passed

    colors = ['#2ecc71', '#e74c3c']
    explode = (0.05, 0.05)

    wedges, texts, autotexts = ax2.pie(
        [total_passed, total_failed],
        labels=['Passed', 'Failed'],
        autopct='%1.1f%%',
        colors=colors,
        explode=explode,
        shadow=True,
        startangle=90
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')
        autotext.set_fontsize(11)

    ax2.set_title(f'Overall Test Results\n{total_passed}/{len(all_results)} Passed',
                  fontsize=12, weight='bold')

    # ========================================================================
    # Plot 3: Test Pass Rate by Category (Top Right)
    # ========================================================================
    ax3 = fig.add_subplot(gs[0, 2])

    pass_rates = []
    for category in categories:
        tests = test_categories[category]
        if tests:
            passed = sum(1 for _, result in tests if result)
            pass_rate = (passed / len(tests)) * 100
            pass_rates.append(pass_rate)

    bars = ax3.barh(categories, pass_rates, color='steelblue', alpha=0.7)
    ax3.set_xlabel('Pass Rate (%)', fontsize=10, weight='bold')
    ax3.set_title('Pass Rate by Category', fontsize=12, weight='bold')
    ax3.set_xlim(0, 100)
    ax3.grid(axis='x', alpha=0.3)

    # Color code bars
    for bar, rate in zip(bars, pass_rates):
        if rate == 100:
            bar.set_color('green')
        elif rate >= 80:
            bar.set_color('yellowgreen')
        elif rate >= 60:
            bar.set_color('orange')
        else:
            bar.set_color('red')

    # Add value labels
    for i, (bar, rate) in enumerate(zip(bars, pass_rates)):
        ax3.text(rate + 2, bar.get_y() + bar.get_height()/2,
                f'{rate:.1f}%',
                va='center', fontsize=9, weight='bold')

    # ========================================================================
    # Plot 4: Failure Analysis - Failed Tests List (Middle Left)
    # ========================================================================
    ax4 = fig.add_subplot(gs[1, :])
    ax4.axis('off')

    failed_tests = [(name, result) for name, result in all_results if not result]

    if failed_tests:
        failure_text = "FAILED TESTS:\n" + "="*100 + "\n"
        for i, (test_name, _) in enumerate(failed_tests, 1):
            failure_text += f"{i}. {test_name}\n"

        ax4.text(0.05, 0.95, failure_text,
                transform=ax4.transAxes,
                fontsize=9,
                verticalalignment='top',
                family='monospace',
                bbox=dict(boxstyle='round', facecolor='mistyrose', alpha=0.8, edgecolor='red', linewidth=2))
        ax4.set_title('Failure Analysis', fontsize=12, weight='bold', pad=10)
    else:
        success_text = "ALL TESTS PASSED!\n\nNo failures to report."
        ax4.text(0.5, 0.5, success_text,
                transform=ax4.transAxes,
                fontsize=14,
                weight='bold',
                ha='center',
                va='center',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8, edgecolor='green', linewidth=2))
        ax4.set_title('Test Status', fontsize=12, weight='bold', pad=10)

    # ========================================================================
    # Plot 5: Model Info & Statistics (Bottom Left)
    # ========================================================================
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.axis('off')

    from deprecated.contourMatching.shapeMatchinModelTraining.modelManager import load_latest_model

    try:
        model = load_latest_model(
            save_dir=r"/home/plp/cobot-soft-v2.1.4/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/GlueDispensingApplication/contourMatching/shapeMatchinModelTraining/saved_models"
        )

        model_info = f"""MODEL INFORMATION
{'='*40}

Model Type: {type(model).__name__}
Training Date: [Check model folder]
Total Tests Run: {len(all_results)}

PERFORMANCE METRICS:
• Total Passed: {total_passed}
• Total Failed: {total_failed}
• Pass Rate: {(total_passed/len(all_results)*100):.1f}%

CATEGORY BREAKDOWN:
"""
        for category, tests in test_categories.items():
            if tests:
                passed = sum(1 for _, result in tests if result)
                model_info += f"• {category}: {passed}/{len(tests)}\n"

        ax5.text(0.05, 0.95, model_info,
                transform=ax5.transAxes,
                fontsize=8,
                verticalalignment='top',
                family='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    except Exception as e:
        ax5.text(0.5, 0.5, f"Model info unavailable:\n{str(e)}",
                transform=ax5.transAxes,
                ha='center',
                va='center',
                fontsize=9)

    ax5.set_title('Model & Statistics', fontsize=12, weight='bold', pad=10)

    # ========================================================================
    # Plot 6: Test Execution Timeline (Bottom Middle)
    # ========================================================================
    ax6 = fig.add_subplot(gs[2, 1])

    # Create a simple timeline visualization
    test_indices = list(range(len(all_results)))
    colors_timeline = ['green' if result else 'red' for _, result in all_results]

    ax6.scatter(test_indices, [1]*len(test_indices), c=colors_timeline, s=100, alpha=0.6)
    ax6.set_xlabel('Test Execution Order', fontsize=10, weight='bold')
    ax6.set_yticks([])
    ax6.set_title('Test Execution Timeline', fontsize=12, weight='bold')
    ax6.grid(axis='x', alpha=0.3)
    ax6.set_xlim(-1, len(all_results))

    # Add legend
    legend_elements = [Patch(facecolor='green', alpha=0.6, label='Pass'),
                      Patch(facecolor='red', alpha=0.6, label='Fail')]
    ax6.legend(handles=legend_elements, loc='upper right')

    # ========================================================================
    # Plot 7: Summary Statistics Box (Bottom Right)
    # ========================================================================
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')

    summary = f"""TEST SUITE SUMMARY
{'='*40}

Total Tests: {len(all_results)}
Passed: {total_passed} ({total_passed/len(all_results)*100:.1f}%)
Failed: {total_failed} ({total_failed/len(all_results)*100:.1f}%)

CATEGORY TOTALS:
"""
    for category, tests in test_categories.items():
        if tests:
            summary += f"• {category}: {len(tests)} tests\n"

    summary += f"\nVISION SIMULATION: {'✓ Enabled' if test_config['use_vision_system_simulation'] else '✗ Disabled'}"
    summary += f"\nCanvas Size: {test_config['canvas_size'][0]}x{test_config['canvas_size'][1]}"

    color = 'lightgreen' if total_failed == 0 else 'lightyellow'
    ax7.text(0.05, 0.95, summary,
            transform=ax7.transAxes,
            fontsize=9,
            verticalalignment='top',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.8, edgecolor='black'))

    ax7.set_title('Summary', fontsize=12, weight='bold', pad=10)

    # Add main title
    fig.suptitle('Test Suite Analysis - Model Performance & Test Clusters',
                fontsize=16, weight='bold', y=0.98)

    # Save the visualization
    output_path = os.path.join(test_config["output_base_dir"], "test_analysis_clusters_model.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved comprehensive analysis: {output_path}")

    plt.close(fig)

    return output_path


def visualize_model_fit_on_test_data(all_results, test_config):
    """
    Visualize how well the model fits the actual test data by:
    1. Extracting features from all test pairs
    2. Plotting them in feature space (using PCA for dimensionality reduction)
    3. Overlaying model predictions vs ground truth
    4. Showing decision boundaries and confidence levels
    """
    print(f"\n{'='*70}")
    print(f"GENERATING MODEL FIT VISUALIZATION")
    print(f"{'='*70}")

    from deprecated.contourMatching.shapeMatchinModelTraining.featuresExtraction import compute_enhanced_features
    from deprecated.contourMatching.shapeMatchinModelTraining.modelManager import load_latest_model, predict_similarity

    # Load model
    try:
        model = load_latest_model(
            save_dir=r"/home/plp/cobot-soft-v2.1.4/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/GlueDispensingApplication/contourMatching/shapeMatchinModelTraining/saved_models"
        )
    except Exception as e:
        print(f"  ✗ Could not load model: {e}")
        return None

    # Collect all test data
    test_data = []

    print(f"  Extracting features from test pairs...")

    # Known matches (should be SAME)
    known_match_shapes = [
        ("Rectangle", create_rectangle_contour),
        ("Triangle", create_triangle_contour),
        ("Pentagon", create_pentagon_contour),
        ("Cross", create_cross_contour),
        ("Star", create_star_contour),
        ("L-Shape", create_l_shape_advanced_contour),
    ]

    for name, shape_func in known_match_shapes:
        try:
            original = shape_func()
            transformed = rotate_contour(original.copy(), 45)
            transformed = translate_contour(transformed, 30, 25)

            # Extract features
            features = compute_enhanced_features(original, transformed)

            # Get model prediction
            result, confidence, proba = predict_similarity(model, original, transformed)

            # Store
            test_data.append({
                'name': f"{name} (Same)",
                'features': features,
                'ground_truth': 'SAME',
                'prediction': result,
                'confidence': confidence,
                'test_passed': (result == 'SAME'),
                'shape_pair': (name, name)
            })
        except Exception as e:
            print(f"    Warning: Could not process {name}: {e}")

    # Known different (should be DIFFERENT)
    known_different_pairs = [
        ("Rectangle", create_rectangle_contour, "Triangle", create_triangle_contour),
        ("Rectangle", create_rectangle_contour, "Star", create_star_contour),
        ("Pentagon", create_pentagon_contour, "Hexagon", create_hexagon_contour),
        ("Cross", create_cross_contour, "Star", create_star_contour),
        ("L-Shape", create_l_shape_advanced_contour, "U-Shape", create_u_shape_advanced_contour),
        ("Convex Blob", create_convex_blob_contour, "Concave Blob", create_concave_blob_contour),
    ]

    for name1, func1, name2, func2 in known_different_pairs:
        try:
            shape1 = func1()
            shape2 = func2()
            shape2 = rotate_contour(shape2, 30)
            shape2 = translate_contour(shape2, 25, 20)

            # Extract features
            features = compute_enhanced_features(shape1, shape2)

            # Get model prediction
            result, confidence, proba = predict_similarity(model, shape1, shape2)

            # Store
            test_data.append({
                'name': f"{name1} vs {name2}",
                'features': features,
                'ground_truth': 'DIFFERENT',
                'prediction': result,
                'confidence': confidence,
                'test_passed': (result == 'DIFFERENT'),
                'shape_pair': (name1, name2)
            })
        except Exception as e:
            print(f"    Warning: Could not process {name1} vs {name2}: {e}")

    if len(test_data) == 0:
        print(f"  ✗ No test data collected")
        return None

    print(f"  Collected {len(test_data)} test samples")

    # Extract features matrix
    X = np.array([d['features'] for d in test_data])

    print(f"  Feature matrix shape: {X.shape}")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply PCA to reduce to 2D for visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    explained_var = pca.explained_variance_ratio_
    print(f"  PCA explained variance: PC1={explained_var[0]:.1%}, PC2={explained_var[1]:.1%}, Total={sum(explained_var):.1%}")

    # Create comprehensive visualization
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

    # ========================================================================
    # Plot 1: Feature Space with Ground Truth (Top Left)
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, 0])

    # Separate by ground truth
    same_mask = np.array([d['ground_truth'] == 'SAME' for d in test_data])
    diff_mask = ~same_mask

    ax1.scatter(X_pca[same_mask, 0], X_pca[same_mask, 1],
               c='green', marker='o', s=100, alpha=0.6, label='Ground Truth: SAME', edgecolors='black')
    ax1.scatter(X_pca[diff_mask, 0], X_pca[diff_mask, 1],
               c='red', marker='s', s=100, alpha=0.6, label='Ground Truth: DIFFERENT', edgecolors='black')

    ax1.set_xlabel(f'PC1 ({explained_var[0]:.1%} variance)', fontsize=11, weight='bold')
    ax1.set_ylabel(f'PC2 ({explained_var[1]:.1%} variance)', fontsize=11, weight='bold')
    ax1.set_title('Feature Space - Ground Truth Labels', fontsize=13, weight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ========================================================================
    # Plot 2: Feature Space with Model Predictions (Top Middle)
    # ========================================================================
    ax2 = fig.add_subplot(gs[0, 1])

    # Separate by prediction
    pred_same_mask = np.array([d['prediction'] == 'SAME' for d in test_data])
    pred_diff_mask = np.array([d['prediction'] == 'DIFFERENT' for d in test_data])
    pred_uncertain_mask = np.array([d['prediction'] == 'UNCERTAIN' for d in test_data])

    if pred_same_mask.any():
        ax2.scatter(X_pca[pred_same_mask, 0], X_pca[pred_same_mask, 1],
                   c='lightgreen', marker='o', s=100, alpha=0.6, label='Predicted: SAME', edgecolors='darkgreen', linewidths=2)
    if pred_diff_mask.any():
        ax2.scatter(X_pca[pred_diff_mask, 0], X_pca[pred_diff_mask, 1],
                   c='lightcoral', marker='s', s=100, alpha=0.6, label='Predicted: DIFFERENT', edgecolors='darkred', linewidths=2)
    if pred_uncertain_mask.any():
        ax2.scatter(X_pca[pred_uncertain_mask, 0], X_pca[pred_uncertain_mask, 1],
                   c='yellow', marker='^', s=100, alpha=0.6, label='Predicted: UNCERTAIN', edgecolors='orange', linewidths=2)

    ax2.set_xlabel(f'PC1 ({explained_var[0]:.1%} variance)', fontsize=11, weight='bold')
    ax2.set_ylabel(f'PC2 ({explained_var[1]:.1%} variance)', fontsize=11, weight='bold')
    ax2.set_title('Feature Space - Model Predictions', fontsize=13, weight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)

    # ========================================================================
    # Plot 3: Correct vs Incorrect Predictions (Top Right)
    # ========================================================================
    ax3 = fig.add_subplot(gs[0, 2])

    # Separate by correctness
    correct_mask = np.array([d['test_passed'] for d in test_data])
    incorrect_mask = ~correct_mask

    if correct_mask.any():
        ax3.scatter(X_pca[correct_mask, 0], X_pca[correct_mask, 1],
                   c='green', marker='o', s=100, alpha=0.7, label='Correct Prediction', edgecolors='black', linewidths=2)
    if incorrect_mask.any():
        ax3.scatter(X_pca[incorrect_mask, 0], X_pca[incorrect_mask, 1],
                   c='red', marker='X', s=150, alpha=0.8, label='Incorrect Prediction', edgecolors='darkred', linewidths=2)

        # Annotate incorrect predictions
        for i, (x, y) in enumerate(X_pca[incorrect_mask]):
            idx = np.where(incorrect_mask)[0][i]
            ax3.annotate(test_data[idx]['name'], (x, y),
                        fontsize=7, ha='center', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

    ax3.set_xlabel(f'PC1 ({explained_var[0]:.1%} variance)', fontsize=11, weight='bold')
    ax3.set_ylabel(f'PC2 ({explained_var[1]:.1%} variance)', fontsize=11, weight='bold')
    ax3.set_title('Model Performance - Correct vs Incorrect', fontsize=13, weight='bold')
    ax3.legend(loc='best', fontsize=10)
    ax3.grid(True, alpha=0.3)

    # ========================================================================
    # Plot 4: Confidence Heatmap (Bottom Left)
    # ========================================================================
    ax4 = fig.add_subplot(gs[1, 0])

    # Create confidence-based colormap
    confidences = np.array([d['confidence'] for d in test_data])

    scatter = ax4.scatter(X_pca[:, 0], X_pca[:, 1],
                         c=confidences, cmap='RdYlGn', s=150, alpha=0.7,
                         edgecolors='black', linewidths=1.5, vmin=0, vmax=1)

    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Model Confidence', fontsize=10, weight='bold')

    ax4.set_xlabel(f'PC1 ({explained_var[0]:.1%} variance)', fontsize=11, weight='bold')
    ax4.set_ylabel(f'PC2 ({explained_var[1]:.1%} variance)', fontsize=11, weight='bold')
    ax4.set_title('Model Confidence Distribution', fontsize=13, weight='bold')
    ax4.grid(True, alpha=0.3)

    # ========================================================================
    # Plot 5: Confusion Matrix (Bottom Middle)
    # ========================================================================
    ax5 = fig.add_subplot(gs[1, 1])

    # Build confusion matrix
    # Map to binary (SAME=1, DIFFERENT/UNCERTAIN=0)
    y_true = np.array([1 if d['ground_truth'] == 'SAME' else 0 for d in test_data])
    y_pred = np.array([1 if d['prediction'] == 'SAME' else 0 for d in test_data])

    cm = confusion_matrix(y_true, y_pred)

    # Plot confusion matrix
    im = ax5.imshow(cm, interpolation='nearest', cmap='Blues')
    ax5.figure.colorbar(im, ax=ax5)

    # Labels
    classes = ['DIFFERENT', 'SAME']
    tick_marks = np.arange(len(classes))
    ax5.set_xticks(tick_marks)
    ax5.set_yticks(tick_marks)
    ax5.set_xticklabels(classes, fontsize=11)
    ax5.set_yticklabels(classes, fontsize=11)

    # Add text annotations
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax5.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center", fontsize=14, weight='bold',
                    color="white" if cm[i, j] > thresh else "black")

    ax5.set_ylabel('Ground Truth', fontsize=11, weight='bold')
    ax5.set_xlabel('Predicted', fontsize=11, weight='bold')
    ax5.set_title('Confusion Matrix', fontsize=13, weight='bold')

    # Calculate accuracy
    accuracy = np.sum(np.diag(cm)) / np.sum(cm)
    ax5.text(0.5, -0.15, f'Accuracy: {accuracy:.1%}',
            transform=ax5.transAxes, ha='center', fontsize=12, weight='bold',
            bbox=dict(boxstyle='round', facecolor='lightgreen' if accuracy > 0.9 else 'yellow', alpha=0.8))

    # ========================================================================
    # Plot 6: Model Performance Statistics (Bottom Right)
    # ========================================================================
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.axis('off')

    # Calculate statistics
    total_tests = len(test_data)
    correct_predictions = sum(1 for d in test_data if d['test_passed'])
    incorrect_predictions = total_tests - correct_predictions

    same_tests = sum(1 for d in test_data if d['ground_truth'] == 'SAME')
    diff_tests = sum(1 for d in test_data if d['ground_truth'] == 'DIFFERENT')

    same_correct = sum(1 for d in test_data if d['ground_truth'] == 'SAME' and d['test_passed'])
    diff_correct = sum(1 for d in test_data if d['ground_truth'] == 'DIFFERENT' and d['test_passed'])

    avg_confidence = np.mean(confidences)
    avg_confidence_correct = np.mean([d['confidence'] for d in test_data if d['test_passed']])
    avg_confidence_incorrect = np.mean([d['confidence'] for d in test_data if not d['test_passed']]) if incorrect_predictions > 0 else 0

    stats_text = f"""MODEL PERFORMANCE STATISTICS
{'='*50}

OVERALL:
• Total Tests: {total_tests}
• Correct Predictions: {correct_predictions} ({correct_predictions/total_tests*100:.1f}%)
• Incorrect Predictions: {incorrect_predictions} ({incorrect_predictions/total_tests*100:.1f}%)
• Overall Accuracy: {accuracy:.1%}

BY CLASS:
• SAME: {same_correct}/{same_tests} correct ({same_correct/same_tests*100 if same_tests > 0 else 0:.1f}%)
• DIFFERENT: {diff_correct}/{diff_tests} correct ({diff_correct/diff_tests*100 if diff_tests > 0 else 0:.1f}%)

CONFIDENCE:
• Average: {avg_confidence:.1%}
• When Correct: {avg_confidence_correct:.1%}
• When Incorrect: {avg_confidence_incorrect:.1%}

FEATURE SPACE:
• Total Features: {X.shape[1]}
• PCA Components: 2
• Variance Explained: {sum(explained_var):.1%}
"""

    if incorrect_predictions > 0:
        stats_text += f"\nMISCLASSIFIED SAMPLES:\n"
        for i, d in enumerate(test_data):
            if not d['test_passed']:
                stats_text += f"• {d['name']}: GT={d['ground_truth']}, Pred={d['prediction']} ({d['confidence']:.1%})\n"

    color = 'lightgreen' if accuracy > 0.9 else 'lightyellow' if accuracy > 0.7 else 'lightcoral'

    ax6.text(0.05, 0.95, stats_text,
            transform=ax6.transAxes,
            fontsize=9,
            verticalalignment='top',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.8, edgecolor='black', linewidth=2))

    ax6.set_title('Performance Summary', fontsize=13, weight='bold', pad=10)

    # Main title
    fig.suptitle('Model Fit Analysis - Feature Space Visualization',
                fontsize=16, weight='bold', y=0.98)

    # Save
    output_path = os.path.join(test_config["output_base_dir"], "model_fit_analysis.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved model fit analysis: {output_path}")

    plt.close(fig)

    return output_path
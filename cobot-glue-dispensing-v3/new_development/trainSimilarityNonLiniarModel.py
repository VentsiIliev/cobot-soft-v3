import cv2
import numpy as np
import random
import itertools
from dataclasses import dataclass
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# ----------------------------
# 1️⃣ Synthetic Contour Dataset
# ----------------------------
@dataclass
class SyntheticContour:
    contour: np.ndarray
    object_id: str
    shape_type: str
    scale: float
    variant_name: str

# ----------------------------
# Parameterized similarity function
# ----------------------------
def _getSimilarity_param(contour1, contour2,
                         MOMENT_THRESHOLD=0.5,
                         AREA_DIFF_THRESHOLD=0.5,
                         CONVEXITY_THRESHOLD=0.3,
                         SHAPE_CONTEXT_THRESHOLD=50.0,
                         MOMENTS_WEIGHT=0.4,
                         CONVEXITY_WEIGHT=0.2,
                         SHAPE_CONTEXT_WEIGHT=0.4,
                         SC_PENALTY_MULTIPLIER=0.01,
                         debug=False):
    contour1 = np.array(contour1, dtype=np.float32)
    contour2 = np.array(contour2, dtype=np.float32)

    # Calculate all features
    moment_diff = cv2.matchShapes(contour1, contour2, cv2.CONTOURS_MATCH_I1, 0.0)
    
    # Area similarity
    area1 = cv2.contourArea(contour1.reshape(-1, 1, 2))
    area2 = cv2.contourArea(contour2.reshape(-1, 1, 2))
    if area1 > 0 and area2 > 0:
        area_ratio = min(area1, area2) / max(area1, area2)
        area_diff = 1 - area_ratio
    else:
        area_diff = 1.0

    # Convexity similarity
    convexity_diff = abs(convexity_ratio(contour1) - convexity_ratio(contour2))

    # Shape context / Hausdorff distance - made more noise-tolerant
    try:
        sc_extractor = cv2.createShapeContextDistanceExtractor()
        sc_distance = sc_extractor.computeDistance(contour1, contour2)
    except AttributeError:
        # Use modified Hausdorff that's more noise tolerant
        sc_distance = noise_tolerant_hausdorff(contour1, contour2)
        # Normalize for noisy data
        sc_distance = min(sc_distance / 50.0, 1.0)

    if debug:
        print(f"moment_diff: {moment_diff:.3f}, area_diff: {area_diff:.3f}, convexity_diff: {convexity_diff:.3f}, sc_distance: {sc_distance:.3f}")

    # Calculate weighted combination (lower is more similar)
    combined_score = (moment_diff * MOMENTS_WEIGHT) + \
                     (area_diff * 0.1) + \
                     (convexity_diff * CONVEXITY_WEIGHT) + \
                     (sc_distance * SHAPE_CONTEXT_WEIGHT)
    
    # Convert to similarity percentage (higher is more similar)
    similarity = max(0, (1 - combined_score) * 100)
    
    if debug:
        print(f"combined_score: {combined_score:.3f}, similarity: {similarity:.1f}%")
    
    return similarity

# ----------------------------
# Shape generation and transforms
# ----------------------------
def generate_shape(shape_type, scale=1.0, img_size=(256, 256)):
    img = np.zeros(img_size, dtype=np.uint8)
    h, w = img_size
    cx, cy = w // 2, h // 2
    base = int(50 * scale)

    if shape_type == "circle":
        cv2.circle(img, (cx, cy), base, 255, -1)
    elif shape_type == "rectangle":
        cv2.rectangle(img, (cx - base, cy - base), (cx + base, cy + base), 255, -1)
    elif shape_type == "triangle":
        pts = np.array([[cx, cy - base], [cx - base, cy + base], [cx + base, cy + base]])
        cv2.drawContours(img, [pts], 0, 255, -1)
    elif shape_type == "convex_blob":
        pts = np.random.randn(8, 2) * base + np.array([cx, cy])
        hull = cv2.convexHull(pts.astype(np.int32))
        cv2.drawContours(img, [hull], 0, 255, -1)
    elif shape_type == "concave_blob":
        pts = np.random.randn(10, 2) * base + np.array([cx, cy])
        hull = cv2.convexHull(pts.astype(np.int32)).squeeze()
        for i in range(0, len(hull), 2):
            hull[i] -= np.random.randint(5, 15, size=2)
        cv2.drawContours(img, [hull.astype(np.int32)], 0, 255, -1)
    elif shape_type == "star":
        pts = []
        for i in range(5):
            angle_outer = i * 2 * np.pi / 5
            angle_inner = angle_outer + np.pi / 5
            outer = [cx + int(base * np.cos(angle_outer)), cy + int(base * np.sin(angle_outer))]
            inner = [cx + int(base / 2 * np.cos(angle_inner)), cy + int(base / 2 * np.sin(angle_inner))]
            pts.append(outer)
            pts.append(inner)
        pts = np.array(pts)
        cv2.drawContours(img, [pts], 0, 255, -1)
    else:
        raise NotImplementedError(f"Shape {shape_type} not implemented")

    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(contours, key=cv2.contourArea)

def rotate_contour(contour, angle_deg):
    pts = contour.reshape(-1, 2)
    cx, cy = np.mean(pts, axis=0)
    rad = np.deg2rad(angle_deg)
    rot = np.array([[np.cos(rad), -np.sin(rad)],
                    [np.sin(rad), np.cos(rad)]])
    rotated = np.dot(pts - [cx, cy], rot.T) + [cx, cy]
    return rotated.reshape(-1, 1, 2).astype(np.float32)

def jitter_contour(contour, noise_level=0.5):
    pts = contour.reshape(-1, 2)
    noise = np.random.normal(scale=noise_level, size=pts.shape)
    return (pts + noise).reshape(-1, 1, 2).astype(np.float32)

# ----------------------------
# Convexity / Hausdorff
# ----------------------------
def convexity_ratio(contour):
    hull = cv2.convexHull(contour)
    return cv2.contourArea(contour) / (cv2.contourArea(hull) + 1e-6)

def hausdorff_distance(c1, c2):
    from scipy.spatial.distance import directed_hausdorff
    pts1 = c1.reshape(-1, 2)
    pts2 = c2.reshape(-1, 2)
    return max(directed_hausdorff(pts1, pts2)[0], directed_hausdorff(pts2, pts1)[0])

def noise_tolerant_hausdorff(c1, c2):
    """
    Noise-tolerant version of Hausdorff distance that:
    1. Uses percentile-based distance instead of max
    2. Smooths contours before comparison
    3. Uses multiple scale comparisons
    """
    from scipy.spatial.distance import cdist
    
    # Smooth contours to reduce noise impact
    pts1 = smooth_contour_points(c1.reshape(-1, 2))
    pts2 = smooth_contour_points(c2.reshape(-1, 2))
    
    # Compute all pairwise distances
    distances = cdist(pts1, pts2)
    
    # Use 95th percentile instead of max (more noise tolerant)
    d1_to_2 = np.percentile(np.min(distances, axis=1), 95)
    d2_to_1 = np.percentile(np.min(distances, axis=0), 95)
    
    return max(d1_to_2, d2_to_1)

def smooth_contour_points(pts, window=3):
    """Apply simple moving average smoothing to contour points"""
    if len(pts) < window:
        return pts
    
    smoothed = np.copy(pts).astype(np.float32)
    for i in range(len(pts)):
        # Get indices for window around current point (circular)
        indices = [(i + j - window//2) % len(pts) for j in range(window)]
        # Average the points in the window
        smoothed[i] = np.mean(pts[indices], axis=0)
    
    return smoothed

# ----------------------------
# Generate dataset and pairs
# ----------------------------
def generate_synthetic_dataset(n_shapes=6, n_variants=5, n_copies=3):
    shape_pool = ["circle", "rectangle", "triangle", "convex_blob", "concave_blob", "star"]
    shape_types = random.sample(shape_pool, n_shapes)
    dataset = []
    for shape in shape_types:
        for variant in range(n_variants):
            base = generate_shape(shape, scale=1.0 + 0.1 * variant)
            for copy in range(n_copies):
                contour = rotate_contour(base, random.uniform(0, 360))
                contour = jitter_contour(contour, 0.5)
                obj_id = f"{shape}_{variant}"
                dataset.append(SyntheticContour(contour, obj_id, shape, 1.0 + 0.1*variant, f"{obj_id}_copy{copy}"))
    return dataset

def generate_balanced_pairs(dataset):
    pairs_pos, pairs_neg = [], []
    grouped = {}
    for s in dataset:
        grouped.setdefault(s.object_id, []).append(s)
    object_ids = list(grouped.keys())
    # positive pairs
    for samples in grouped.values():
        for a, b in itertools.combinations(samples, 2):
            pairs_pos.append((a.contour, b.contour))
    # negative pairs
    for i in range(len(object_ids)):
        for j in range(i+1, len(object_ids)):
            samples_a = grouped[object_ids[i]]
            samples_b = grouped[object_ids[j]]
            for a in samples_a:
                for b in samples_b:
                    pairs_neg.append((a.contour, b.contour))
    # balance
    n = min(len(pairs_pos), len(pairs_neg))
    pairs_pos = random.sample(pairs_pos, n)
    pairs_neg = random.sample(pairs_neg, n)
    pairs = pairs_pos + pairs_neg
    labels = [1]*n + [0]*n
    combined = list(zip(pairs, labels))
    random.shuffle(combined)
    pairs, labels = zip(*combined)
    return list(pairs), list(labels)

# ----------------------------
# Loss function for weight optimization
# ----------------------------
def loss_function_weights(params, pairs, labels):
    MOMENTS_WEIGHT, CONVEXITY_WEIGHT, SHAPE_CONTEXT_WEIGHT = params
    total = MOMENTS_WEIGHT + CONVEXITY_WEIGHT + SHAPE_CONTEXT_WEIGHT
    MOMENTS_WEIGHT /= total
    CONVEXITY_WEIGHT /= total
    SHAPE_CONTEXT_WEIGHT /= total
    loss = 0.0
    for (c1, c2), label in zip(pairs, labels):
        sim = _getSimilarity_param(c1, c2,
                                   MOMENTS_WEIGHT=MOMENTS_WEIGHT,
                                   CONVEXITY_WEIGHT=CONVEXITY_WEIGHT,
                                   SHAPE_CONTEXT_WEIGHT=SHAPE_CONTEXT_WEIGHT)
        sim_norm = sim / 100.0
        loss += (sim_norm - label)**2
    return loss / len(pairs)

# ----------------------------
# Visualization of contour pairs
# ----------------------------
def visualize_pairs(pairs, labels, weights, n_samples=5):
    for i, ((c1, c2), label) in enumerate(zip(pairs, labels)):
        if i >= n_samples:
            break
        print(f"\n--- Pair {i+1} Debug ---")
        sim = _getSimilarity_param(c1, c2,
                                   MOMENTS_WEIGHT=weights[0],
                                   CONVEXITY_WEIGHT=weights[1],
                                   SHAPE_CONTEXT_WEIGHT=weights[2],
                                   debug=True)
        print(f"Expected: {'MATCH' if label==1 else 'NO MATCH'}, Got: {sim:.1f}%")
        
        plt.figure(figsize=(6,3))
        plt.subplot(1,2,1)
        pts = c1.reshape(-1,2)
        plt.plot(pts[:,0], pts[:,1],'b-')
        plt.gca().invert_yaxis()
        plt.title("Contour 1")
        plt.subplot(1,2,2)
        pts = c2.reshape(-1,2)
        plt.plot(pts[:,0], pts[:,1],'r-')
        plt.gca().invert_yaxis()
        color = 'green' if label==1 else 'red'
        plt.title(f"Sim={sim:.1f}% | {'MATCH' if label==1 else 'NO MATCH'}", color=color)
        plt.tight_layout()
        plt.show()

# ----------------------------
# Run pipeline
# ----------------------------
if __name__ == "__main__":
    dataset = generate_synthetic_dataset()
    pairs, labels = generate_balanced_pairs(dataset)

    # Optimize weights
    init_params = [0.4, 0.3, 0.3]
    bounds = [(0,1),(0,1),(0,1)]
    res = minimize(loss_function_weights, init_params, args=(pairs, labels), bounds=bounds, method='L-BFGS-B')
    best_weights = res.x
    best_weights /= best_weights.sum()
    print("✅ Optimized weights (sum normalized):")
    print(f"  Moments weight:      {best_weights[0]:.6f}")
    print(f"  Convexity weight:    {best_weights[1]:.6f}")
    print(f"  Shape context weight: {best_weights[2]:.6f}")
    print(f"  Total: {best_weights.sum():.6f}")

    # Test and visualize pairs
    visualize_pairs(pairs, labels, best_weights, n_samples=5)
    
    # Additional test: Compare shapes with themselves
    print("\n🔍 Self-similarity test (should be close to 100%):")
    test_samples = random.sample(dataset, 5)
    for i, sample in enumerate(test_samples):
        self_sim = _getSimilarity_param(sample.contour, sample.contour,
                                       MOMENTS_WEIGHT=best_weights[0],
                                       CONVEXITY_WEIGHT=best_weights[1], 
                                       SHAPE_CONTEXT_WEIGHT=best_weights[2])
        print(f"  {sample.variant_name}: {self_sim:.1f}%")

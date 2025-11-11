import cv2
import numpy as np
from scipy.spatial.distance import directed_hausdorff

# ===== AREA FEATURES =====

def equivalent_diameter_diff(c1, c2):
    """Compute difference in equivalent diameters (R/T invariant, scale sensitive)"""
    area1 = cv2.contourArea(c1)
    area2 = cv2.contourArea(c2)
    
    # Equivalent diameter = sqrt(4*Area/pi)
    eq_diam1 = np.sqrt(4 * area1 / np.pi) if area1 > 0 else 0
    eq_diam2 = np.sqrt(4 * area2 / np.pi) if area2 > 0 else 0
    
    return abs(eq_diam1 - eq_diam2)

def scale_band_categorical(area1, area2, bands=5):
    """Classify areas into discrete bands and return categorical difference"""
    # Define scale bands (can be adjusted based on your scale ranges)
    max_area = max(area1, area2, 10000)  # Ensure reasonable max
    band_size = max_area / bands
    
    band1 = min(int(area1 / band_size), bands - 1)
    band2 = min(int(area2 / band_size), bands - 1)
    
    return abs(band1 - band2) / (bands - 1)  # Normalize to 0-1

# ===== GEOMETRIC FEATURES =====

def aspect_ratio(contour):
    """Aspect ratio of bounding rectangle"""
    x, y, w, h = cv2.boundingRect(contour)
    if h == 0: return 0
    return w / h

def extent(contour):
    """Extent = contour area / bounding rectangle area"""
    area = cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)
    rect_area = w * h
    if rect_area == 0: return 0
    return area / rect_area

def solidity(contour):
    """Solidity = contour area / convex hull area"""
    hull = cv2.convexHull(contour)
    if cv2.contourArea(hull) == 0: return 0
    return cv2.contourArea(contour) / cv2.contourArea(hull)

def convexity_ratio(contour):
    hull = cv2.convexHull(contour)
    if cv2.contourArea(hull) == 0: return 0
    return cv2.contourArea(contour) / cv2.contourArea(hull)

def convexity_defects_count(contour):
    """Return number of convexity defects safely (handles degenerate contours)."""
    if contour is None:
        return 0

    pts = np.asarray(contour)
    if pts.size == 0:
        return 0

    # Normalize to (N, 2)
    try:
        pts = pts.reshape(-1, 2)
    except Exception:
        return 0

    # Need at least 4 points to have meaningful convexity defects
    if pts.shape[0] < 4:
        return 0

    # Prepare OpenCV-friendly contour shape and dtype
    contour_cv = pts.reshape(-1, 1, 2).astype(np.int32)

    try:
        # returnPoints=False -> indices into contour_cv
        hull = cv2.convexHull(contour_cv, returnPoints=False)
        if hull is None or len(hull) < 3:
            return 0

        hull = hull.astype(np.int32)

        defects = cv2.convexityDefects(contour_cv, hull)
        if defects is None:
            return 0

        return int(defects.shape[0])
    except cv2.error:
        # OpenCV assertion / runtime errors -> treat as no defects
        return 0
    except Exception:
        return 0

def perimeter_features(contour):
    """Perimeter-based features"""
    perimeter = cv2.arcLength(contour, True)
    area = cv2.contourArea(contour)
    if perimeter == 0 or area == 0:
        return [0, 0]

    # Circularity: 4π*area/perimeter²
    circularity = 4 * np.pi * area / (perimeter ** 2)

    # Compactness: perimeter²/area
    compactness = perimeter ** 2 / area

    return [circularity, compactness]

# ===== LOCAL FEATURES =====

# python
def compute_curvature_features(contour, n_bins=20):
    """Compute local curvature histogram features (robust to degenerate contours)."""
    pts = np.asarray(contour).squeeze()
    if pts.size == 0 or pts.ndim != 2 or pts.shape[0] < 3:
        return [0.0] * n_bins

    x = pts[:, 0].astype(float)
    y = pts[:, 1].astype(float)

    dx = np.gradient(x)
    dy = np.gradient(y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)

    denom = np.power(dx**2 + dy**2, 1.5)

    # Safely compute curvature without noisy divide warnings
    with np.errstate(divide='ignore', invalid='ignore'):
        curvature = np.abs(dx * ddy - dy * ddx) / denom

    # Replace NaN/inf with zeros
    curvature = np.nan_to_num(curvature, nan=0.0, posinf=0.0, neginf=0.0)

    # Use percentile-based upper bound; if non-positive use zero histogram
    if curvature.size == 0:
        return [0.0] * n_bins

    p95 = np.percentile(curvature, 95)
    if p95 <= 0:
        return [0.0] * n_bins

    hist, _ = np.histogram(curvature, bins=n_bins, range=(0.0, p95))
    s = hist.sum()
    if s > 0:
        hist = hist.astype(float) / s
    else:
        hist = np.zeros(n_bins, dtype=float)

    return hist.tolist()


def hausdorff_distance(c1, c2):
    """Compute simple Hausdorff distance manually."""
    pts1 = c1.reshape(-1, 2)
    pts2 = c2.reshape(-1, 2)
    return max(
        directed_hausdorff(pts1, pts2)[0],
        directed_hausdorff(pts2, pts1)[0]
    )

def detect_harris_corners(contour, img_size=100, block_size=2, k_param=0.04, threshold=0.02):
    """
    Detect Harris corners in a contour using corner detection.
    
    Args:
        contour: Input contour
        img_size: Size of temporary image for corner detection
        block_size: Neighborhood size for Harris detector
        k_param: Harris detector free parameter
        threshold: Threshold for corner detection (relative to max response)
        
    Returns:
        dict: Corner statistics including count, responses, and density
    """
    # Early termination for simple contours
    contour_points = contour.reshape(-1, 2)
    if len(contour_points) < 4:
        return {'corner_count': 0, 'corner_responses': [], 'corner_density': 0, 
                'response_mean': 0, 'response_max': 0, 'response_var': 0}
    
    # Create a temporary image with the contour
    img = np.zeros((img_size, img_size), dtype=np.uint8)
    
    # Get contour bounds and scale to fit image
    x, y, w, h = cv2.boundingRect(contour)
    if w == 0 or h == 0:
        return {'corner_count': 0, 'corner_responses': [], 'corner_density': 0, 
                'response_mean': 0, 'response_max': 0, 'response_var': 0}
    
    # Scale contour to fit in image with some padding
    padding = 20
    scale_x = (img_size - 2 * padding) / w
    scale_y = (img_size - 2 * padding) / h
    scale = min(scale_x, scale_y)
    
    # Transform contour points
    contour_scaled = contour.copy().astype(np.float32)
    contour_scaled[:, :, 0] = (contour_scaled[:, :, 0] - x) * scale + padding + (img_size - w * scale) / 2
    contour_scaled[:, :, 1] = (contour_scaled[:, :, 1] - y) * scale + padding + (img_size - h * scale) / 2
    contour_scaled = contour_scaled.astype(np.int32)
    
    # Draw filled contour
    cv2.fillPoly(img, [contour_scaled], 255)
    
    # Detect Harris corners (removed Gaussian blur for speed)
    try:
        corners = cv2.cornerHarris(img, block_size, 3, k_param)
        
        # Find corner points above threshold
        corner_threshold = threshold * corners.max() if corners.max() > 0 else 0
        corner_points = np.where(corners > corner_threshold)
        
        if len(corner_points[0]) == 0:
            return {'corner_count': 0, 'corner_responses': [], 'corner_density': 0,
                    'response_mean': 0, 'response_max': 0, 'response_var': 0}
        
        # Get corner responses
        corner_responses = corners[corner_points]
        corner_responses = corner_responses[corner_responses > 0]  # Only positive responses
        
        # Apply non-maximum suppression to get distinct corners (vectorized)
        corner_coords = np.column_stack(corner_points)
        if len(corner_coords) > 1:
            min_distance = max(5, int(scale * 10))  # Minimum distance between corners
            
            # Vectorized distance computation
            from scipy.spatial.distance import pdist, squareform
            distances = squareform(pdist(corner_coords))
            
            # Find corners that are local maxima
            corner_responses_full = corners[corner_points]
            keep_mask = np.ones(len(corner_coords), dtype=bool)
            
            # Sort by response strength (highest first)
            sorted_indices = np.argsort(corner_responses_full)[::-1]
            
            for i in sorted_indices:
                if not keep_mask[i]:
                    continue
                # Suppress nearby weaker corners
                nearby = (distances[i] < min_distance) & (distances[i] > 0)
                weaker = corner_responses_full < corner_responses_full[i]
                keep_mask[nearby & weaker] = False
            
            if np.any(keep_mask):
                corner_responses = corner_responses_full[keep_mask]
            else:
                corner_responses = corner_responses_full[:1]  # Keep at least one corner
        
        # Calculate statistics
        corner_count = len(corner_responses)
        perimeter = cv2.arcLength(contour, True)
        corner_density = corner_count / perimeter if perimeter > 0 else 0
        
        response_mean = np.mean(corner_responses) if len(corner_responses) > 0 else 0
        response_max = np.max(corner_responses) if len(corner_responses) > 0 else 0
        response_var = np.var(corner_responses) if len(corner_responses) > 0 else 0
        
        return {
            'corner_count': corner_count,
            'corner_responses': corner_responses.tolist(),
            'corner_density': corner_density,
            'response_mean': response_mean,
            'response_max': response_max,
            'response_var': response_var
        }
        
    except Exception as e:
        # Return default values on error
        return {'corner_count': 0, 'corner_responses': [], 'corner_density': 0,
                'response_mean': 0, 'response_max': 0, 'response_var': 0}

# ===== GLOBAL FEATURES =====

def hu_moments_features(contour):
    """Compute Hu moments - rotation, scale, translation invariant"""
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()
    # Log transform to make them more manageable
    hu = -np.sign(hu) * np.log10(np.abs(hu) + 1e-10)
    return hu

def fourier_descriptors(contour, n_descriptors=24):
    pts = contour.reshape(-1, 2)
    if len(pts) < n_descriptors + 1:
        # Repeat points to pad
        pad_len = (n_descriptors + 1) - len(pts)
        pts = np.vstack([pts, np.tile(pts[-1], (pad_len, 1))])
    center = np.mean(pts, axis=0)
    pts_centered = pts - center
    complex_pts = pts_centered[:, 0] + 1j * pts_centered[:, 1]
    fft_vals = np.fft.fft(complex_pts)
    descriptors = np.abs(fft_vals[1:n_descriptors + 1])
    if len(descriptors) > 0 and descriptors[0] != 0:
        descriptors = descriptors / descriptors[0]
    return descriptors

# ===== FEATURE GROUP FUNCTIONS =====

def get_area_features(c1, c2):
    """Extract area-related features (5 features)"""
    area1 = cv2.contourArea(c1)
    area2 = cv2.contourArea(c2)
    perimeter1 = cv2.arcLength(c1, True)
    perimeter2 = cv2.arcLength(c2, True)
    
    # Scale-sensitive features (R/T invariant)
    absolute_area_diff = abs(area1 - area2)
    absolute_perimeter_diff = abs(perimeter1 - perimeter2)
    scale_band_diff = scale_band_categorical(area1, area2)
    equiv_diameter_diff = equivalent_diameter_diff(c1, c2)
    area_ratio = abs(area1 - area2) / max(area1, area2)
    
    return [absolute_area_diff, absolute_perimeter_diff, scale_band_diff, equiv_diameter_diff, area_ratio]

def get_geometric_features(c1, c2):
    """Extract geometric shape features (3 features)"""
    solidity_diff = abs(solidity(c1) - solidity(c2))
    extent_diff = abs(extent(c1) - extent(c2))
    aspect_ratio_diff = abs(aspect_ratio(c1) - aspect_ratio(c2))
    
    return [solidity_diff, extent_diff, aspect_ratio_diff]

def get_local_features(c1, c2, n_curv_bins=16):
    """Extract local/point-wise features (n_curv_bins features)"""
    # Curvature histogram differences
    curv1 = compute_curvature_features(c1, n_bins=n_curv_bins)
    curv2 = compute_curvature_features(c2, n_bins=n_curv_bins)
    curv_diff = np.abs(np.array(curv1) - np.array(curv2))
    
    return curv_diff.tolist()

def get_global_features(c1, c2):
    """Extract global shape features (15 features: 7 Hu + 8 Fourier)"""
    features = []
    
    # Hu moments differences (7 features)
    try:
        hu1 = hu_moments_features(c1)
        hu2 = hu_moments_features(c2)
        if len(hu1) != 7 or len(hu2) != 7:
            raise ValueError(f"Hu moments must return exactly 7 values. Got hu1={len(hu1)}, hu2={len(hu2)}")

        hu_diff = np.abs(hu1 - hu2)
        if np.any(np.isnan(hu_diff)) or np.any(np.isinf(hu_diff)):
            raise ValueError(f"Hu moments calculation produced invalid values: {hu_diff}")

        features.extend(hu_diff.tolist())
    except Exception as e:
        raise RuntimeError(f"Hu moments feature extraction failed: {str(e)}. Contour shapes: c1={c1.shape}, c2={c2.shape}")

    # Fourier descriptors differences (8 features)
    try:
        fourier1 = fourier_descriptors(c1, 8)
        fourier2 = fourier_descriptors(c2, 8)
        if len(fourier1) != 8 or len(fourier2) != 8:
            raise ValueError(f"Fourier descriptors must return exactly 8 values. Got fourier1={len(fourier1)}, fourier2={len(fourier2)}")

        fourier_diff = np.abs(fourier1 - fourier2)
        if np.any(np.isnan(fourier_diff)) or np.any(np.isinf(fourier_diff)):
            raise ValueError(f"Fourier descriptors calculation produced invalid values: {fourier_diff}")

        features.extend(fourier_diff.tolist())
    except Exception as e:
        raise RuntimeError(f"Fourier descriptors extraction failed: {str(e)}. Contour shapes: c1={c1.shape}, c2={c2.shape}")
    
    return features

def get_shape_similarity_features(c1, c2):
    """Extract shape similarity features (3 features)"""
    area1 = cv2.contourArea(c1)
    area2 = cv2.contourArea(c2)
    perimeter1 = cv2.arcLength(c1, True)
    perimeter2 = cv2.arcLength(c2, True)
    
    # Shape matching
    try:
        m = cv2.matchShapes(c1, c2, cv2.CONTOURS_MATCH_I1, 0.0)
        if np.isnan(m) or np.isinf(m):
            raise ValueError(f"cv2.matchShapes returned invalid value: {m}. Check contour validity.")
    except Exception as e:
        if "invalid value" in str(e):
            raise e
        raise RuntimeError(f"cv2.matchShapes failed: {str(e)}. Contour shapes: c1={c1.shape}, c2={c2.shape}")

    # Convexity difference
    conv_diff = abs(convexity_ratio(c1) - convexity_ratio(c2))

    # Hausdorff distance (normalized by perimeter to be scale-relative)
    try:
        hausdorff = hausdorff_distance(c1, c2)
        if np.isnan(hausdorff) or np.isinf(hausdorff):
            raise ValueError(f"Hausdorff distance calculation returned invalid value: {hausdorff}. Check contour point validity.")
        # Normalize by average perimeter to make it scale-relative
        hausdorff_normalized = hausdorff / ((perimeter1 + perimeter2) / 2) if (perimeter1 + perimeter2) > 0 else 0
    except Exception as e:
        if "invalid value" in str(e):
            raise e
        raise RuntimeError(f"Hausdorff distance calculation failed: {str(e)}. Contour shapes: c1={c1.shape}, c2={c2.shape}")

    return [m, conv_diff, hausdorff_normalized]

def get_perimeter_features(c1, c2):
    """Extract perimeter-based features (2 features)"""
    try:
        perim1 = perimeter_features(c1)
        perim2 = perimeter_features(c2)
        if len(perim1) != 2 or len(perim2) != 2:
            raise ValueError(f"Perimeter features must return exactly 2 values. Got perim1={len(perim1)}, perim2={len(perim2)}")

        perim_diff = np.abs(np.array(perim1) - np.array(perim2))
        if np.any(np.isnan(perim_diff)) or np.any(np.isinf(perim_diff)):
            raise ValueError(f"Perimeter features calculation produced invalid values: {perim_diff}")

        return perim_diff.tolist()
    except Exception as e:
        raise RuntimeError(f"Perimeter features extraction failed: {str(e)}. Contour shapes: c1={c1.shape}, c2={c2.shape}")

def get_convexity_features(c1, c2):
    """Extract convexity-based features (2 features)"""
    # Convexity defect difference
    hull1 = cv2.convexHull(c1)
    hull2 = cv2.convexHull(c2)
    convex_def1 = 1 - cv2.contourArea(c1) / cv2.contourArea(hull1)
    convex_def2 = 1 - cv2.contourArea(c2) / cv2.contourArea(hull2)
    convex_def_diff = abs(convex_def1 - convex_def2)
    
    # Convexity defects count difference
    defects1 = convexity_defects_count(c1)
    defects2 = convexity_defects_count(c2)
    defects_count_diff = abs(defects1 - defects2)
    
    return [convex_def_diff, defects_count_diff]

def get_corner_features(c1, c2):
    """Extract Harris corner detection features (5 features)"""
    try:
        # Detect corners for both contours
        corners1 = detect_harris_corners(c1)
        corners2 = detect_harris_corners(c2)
        
        # Extract feature differences
        corner_count_diff = abs(corners1['corner_count'] - corners2['corner_count'])
        corner_density_diff = abs(corners1['corner_density'] - corners2['corner_density'])
        response_mean_diff = abs(corners1['response_mean'] - corners2['response_mean'])
        response_max_diff = abs(corners1['response_max'] - corners2['response_max'])
        response_var_diff = abs(corners1['response_var'] - corners2['response_var'])
        
        return [corner_count_diff, corner_density_diff, response_mean_diff, response_max_diff, response_var_diff]
        
    except Exception as e:
        # Return zero differences on error (shapes treated as similar in corner aspect)
        return [0.0, 0.0, 0.0, 0.0, 0.0]

# ===== UTILITY FUNCTIONS =====

def get_feature_extraction_metadata(n_curv_bins=16):
    """Get metadata about the current feature extraction configuration"""
    feature_groups = {
        'area_features': 5,
        'shape_similarity_features': 3,
        'geometric_features': 3,
        'global_features': 15,  # 7 Hu + 8 Fourier
        'perimeter_features': 2,
        'local_features': n_curv_bins,  # Curvature histogram
        'convexity_features': 2,
        'corner_features': 5  # Harris corner detection - NEW!
    }
    
    total_features = sum(feature_groups.values())
    
    return {
        'feature_extraction_version': '2.0',  # Updated for Harris corners
        'total_features': total_features,
        'curvature_bins': n_curv_bins,
        'feature_groups': feature_groups,
        'feature_group_descriptions': {
            'area_features': 'Area, perimeter, scale-sensitive measurements',
            'shape_similarity_features': 'Shape matching, convexity, Hausdorff distance',
            'geometric_features': 'Solidity, extent, aspect ratio',
            'global_features': 'Hu moments (7) + Fourier descriptors (8)',
            'perimeter_features': 'Circularity and compactness',
            'local_features': f'Curvature histogram with {n_curv_bins} bins',
            'convexity_features': 'Convexity defects and convex hull differences',
            'corner_features': 'Harris corner detection: count, density, response stats'
        },
        'new_in_v2': ['corner_features'],
        'corner_detection_params': {
            'img_size': 100,  # Optimized: reduced from 200 for speed
            'block_size': 2,
            'k_param': 0.04,
            'threshold': 0.02,  # Optimized: increased threshold for speed
            'optimizations': ['vectorized_nms', 'early_termination', 'no_blur']
        }
    }

def compute_features_parallel(pair,n_curv_bins=16):
    """Wrapper function for parallel feature computation"""
    return compute_enhanced_features(pair[0], pair[1],n_curv_bins)


def compute_enhanced_features(c1, c2, n_curv_bins=16):
    """Enhanced feature extraction for non-linear models with scale sensitivity."""
    # Validate input contours
    area1 = cv2.contourArea(c1)
    area2 = cv2.contourArea(c2)
    if area1 <= 0 or area2 <= 0:
        raise ValueError(f"Invalid contour areas: c1_area={area1}, c2_area={area2}. Contours must have positive area.")
    
    # Extract features using category-specific functions
    features = []
    
    # 1. Area features (5 features)
    area_features = get_area_features(c1, c2)
    features.extend(area_features)
    
    # 2. Shape similarity features (3 features)
    shape_features = get_shape_similarity_features(c1, c2)
    features.extend(shape_features)
    
    # 3. Geometric features (3 features)
    geometric_features = get_geometric_features(c1, c2)
    features.extend(geometric_features)
    
    # 4. Global features (15 features: 7 Hu + 8 Fourier)
    global_features = get_global_features(c1, c2)
    features.extend(global_features)
    
    # 5. Perimeter features (2 features)
    perimeter_features = get_perimeter_features(c1, c2)
    features.extend(perimeter_features)
    
    # 6. Local features (n_curv_bins features)
    local_features = get_local_features(c1, c2, n_curv_bins)
    features.extend(local_features)
    
    # 7. Convexity features (2 features)
    convexity_features = get_convexity_features(c1, c2)
    features.extend(convexity_features)
    
    # 8. Corner features (5 features)
    corner_features = get_corner_features(c1, c2)
    features.extend(corner_features)

    # Feature count validation
    expected_count = 5 + 3 + 3 + 15 + 2 + n_curv_bins + 2 + 5  # 35 + n_curv_bins (default 51)
    if len(features) != expected_count:
        raise ValueError(f"Feature extraction must return exactly {expected_count} features, got {len(features)}. "
                        f"Current structure: 5 area + 3 shape + 3 geometric + 15 global + 2 perimeter + {n_curv_bins} local + 2 convexity + 5 corner = {expected_count}")

    # Ensure features is a list
    if not isinstance(features, list):
        features = list(features)

    # Final validation
    features_arr = np.array(features)
    if np.any(np.isnan(features_arr)) or np.any(np.isinf(features_arr)):
        raise ValueError(f"Feature extraction produced invalid values (nan/inf): {features_arr}")

    return features_arr.tolist()

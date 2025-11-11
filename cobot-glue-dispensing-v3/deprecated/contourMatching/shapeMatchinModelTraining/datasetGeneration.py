import cv2
import numpy as np
import random
from dataclasses import dataclass
from shapeGenerator import generate_shape
# ======================================================
# 📊 Synthetic Contour Dataset Generation
# ======================================================

def render_contour_to_canvas(contour, canvas_size=(1280, 720), fill_value=255):
    """
    Render a contour onto a blank canvas and detect it using OpenCV findContours.
    This simulates the real vision system pipeline.

    This function is CRITICAL for creating realistic training data that matches
    what the vision system actually produces. Without this, the model learns
    from "perfect" synthetic contours that don't match real camera data.

    Args:
        contour: Input contour (N, 1, 2) array
        canvas_size: Size of the canvas (width, height) - should match camera resolution
        fill_value: Value to fill the contour with (255 for white)

    Returns:
        Detected contour from cv2.findContours (realistic vision system output)

    Note:
        - Converts float coordinates to int (simulates pixel quantization)
        - Rasterizes the shape (creates jagged edges from smooth curves)
        - Re-detects using findContours (adds/removes points based on edge detection)
        - This process can dramatically change point count, especially for curved shapes
    """
    # Create blank canvas
    canvas = np.zeros((canvas_size[1], canvas_size[0]), dtype=np.uint8)

    # Convert contour to integer coordinates for drawing (simulates pixel quantization)
    contour_int = np.array(contour, dtype=np.int32)

    # Draw filled contour on canvas
    cv2.drawContours(canvas, [contour_int], -1, fill_value, thickness=cv2.FILLED)

    # Find contours using the same method as real vision system
    # RETR_EXTERNAL: Only outer contours (no holes)
    # CHAIN_APPROX_SIMPLE: Compresses horizontal/vertical/diagonal segments
    contours, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        raise ValueError("No contours detected! Contour might be outside canvas bounds.")

    # Return the largest contour (should be the only one in most cases)
    largest_contour = max(contours, key=cv2.contourArea)

    # Convert back to float32 for consistency with the rest of the pipeline
    return np.array(largest_contour, dtype=np.float32)

@dataclass
class SyntheticContour:
    contour: np.ndarray
    object_id: str
    shape_type: str
    scale: float
    variant_name: str



def rotate_contour(contour, angle_deg):
    """Rotate contour by specified angle in degrees"""
    pts = contour.reshape(-1, 2)
    cx, cy = np.mean(pts, axis=0)
    rad = np.deg2rad(angle_deg)
    rot = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
    rotated = np.dot(pts - [cx, cy], rot.T) + [cx, cy]
    return rotated.reshape(-1, 1, 2).astype(np.float32)

def jitter_contour(contour, noise_level=0.2):
    """Add random noise to contour points"""
    pts = contour.reshape(-1, 2)
    noise = np.random.normal(scale=noise_level, size=pts.shape)
    return (pts + noise).reshape(-1, 1, 2).astype(np.float32)

def deform_contour(contour, deform_strength=0.01):
    """Apply random deformation to contour"""
    pts = contour.reshape(-1, 2)
    for i in range(len(pts)):
        pts[i] += np.random.randn(2) * deform_strength * 100
    return pts.reshape(-1, 1, 2).astype(np.float32)

def simplify_contour(contour, epsilon_ratio=0.01):
    """Simplify contour using Douglas-Peucker algorithm"""
    epsilon = epsilon_ratio * cv2.arcLength(contour, True)
    return cv2.approxPolyDP(contour, epsilon, True)

def get_all_shape_types():
    """Get list of all available shape types"""
    return [
        # Basic geometric shapes
        "circle", "ellipse", "rectangle", "square", "triangle", "diamond",
        "hexagon", "octagon", "pentagon",
        
        # Hard negatives - similar but different shapes
        "oval", "rounded_rect", "rounded_corner_rect",  # Similar to circle/rectangle
        
        # Special shapes
        "s_shape", "c_shape", "t_shape", "u_shape", "l_shape",
        
        # Complex shapes
        "star", "cross", "arrow", "heart", "crescent",
        
        # Industrial/mechanical shapes
        "gear", "donut", "trapezoid", "parallelogram", "hourglass", "lightning"
    ]

def get_hard_negative_pairs():
    """Define pairs of similar-looking but different shapes for hard negative training"""
    return [
        ("circle", "oval"),
        ("circle", "octagon"), 
        ("rectangle", "rounded_rect"),
        ("rectangle", "parallelogram"),
        ("rectangle", "rounded_corner_rect"),  # Rectangle vs rectangle with one rounded corner
        ("hexagon", "pentagon"),
        ("hexagon", "octagon"),
        ("triangle", "arrow"),
        ("square", "diamond"),
        ("ellipse", "oval")
    ]

def generate_synthetic_dataset(n_shapes=8, n_scales=3, n_variants=5, n_noisy=4, include_hard_negatives=True, use_vision_simulation=True, canvas_size=(1280, 720)):
    """
    Generate synthetic contour dataset with specified parameters

    Args:
        n_shapes: Number of different shape types to use
        n_scales: Number of different scales per shape
        n_variants: Number of rotation variants per scale
        n_noisy: Number of noise variants per rotation
        include_hard_negatives: Whether to ensure hard negative pairs are included
        use_vision_simulation: If True, process contours through vision system simulation.
                              This is CRITICAL for training a model that works with real camera data.
        canvas_size: Size of the canvas for vision simulation (width, height).
                    Should match your camera resolution (default: 1280x720)

    Returns:
        List of SyntheticContour objects
    """
    all_shapes = get_all_shape_types()
    
    if include_hard_negatives:
        # Ensure hard negative pairs are included in the selected shapes
        hard_pairs = get_hard_negative_pairs()
        hard_shapes = set()
        for pair in hard_pairs:
            hard_shapes.add(pair[0])
            hard_shapes.add(pair[1])
        
        # Start with hard negative shapes, then add random ones
        priority_shapes = list(hard_shapes)
        remaining_shapes = [s for s in all_shapes if s not in hard_shapes]
        
        if n_shapes <= len(priority_shapes):
            shape_types = random.sample(priority_shapes, n_shapes)
        else:
            # Include all hard negative shapes, then sample from remaining
            additional_needed = n_shapes - len(priority_shapes)
            additional_shapes = random.sample(remaining_shapes, min(additional_needed, len(remaining_shapes)))
            shape_types = priority_shapes + additional_shapes
        
        print(f"🎯 Selected shapes (hard negatives prioritized): {shape_types}")
        print(f"🔗 Hard negative pairs included: {[pair for pair in hard_pairs if pair[0] in shape_types and pair[1] in shape_types]}")
    else:
        shape_types = random.sample(all_shapes, min(n_shapes, len(all_shapes)))
        print(f"🎯 Selected shapes for training: {shape_types}")
    
    total_samples = len(shape_types) * n_scales * n_variants * n_noisy
    print(f"📊 Generating {total_samples:,} total samples...")
    if use_vision_simulation:
        print(f"🎥 Vision simulation ENABLED - contours will be processed through render→detect pipeline")
        print(f"   Canvas size: {canvas_size[0]}x{canvas_size[1]} pixels")
    else:
        print(f"⚠️  Vision simulation DISABLED - using raw synthetic contours")

    dataset = []
    sample_count = 0
    vision_errors = 0

    for shape_idx, shape in enumerate(shape_types):
        print(f"🔄 Processing shape {shape_idx+1}/{len(shape_types)}: {shape}")

        for scale_idx in range(n_scales):
            # Expanded scale range for better scale discrimination (0.3x to 2.0x)
            scale = 0.3 + scale_idx * (1.7 / max(1, n_scales - 1))  # Distributed across 0.3-2.0
            base = generate_shape(shape, scale)
            obj_id = f"{shape}_scale{scale_idx}"

            for variant in range(n_variants):
                rot = rotate_contour(base, random.uniform(0, 360))
                for noise in range(n_noisy):
                    c = jitter_contour(rot, 0.2)
                    c = deform_contour(c, 0.01)
                    c = simplify_contour(c)

                    # Apply vision system simulation if enabled
                    if use_vision_simulation:
                        try:
                            c = render_contour_to_canvas(c, canvas_size=canvas_size)
                        except ValueError as e:
                            # Contour might be outside canvas bounds - skip this sample
                            vision_errors += 1
                            continue

                    dataset.append(SyntheticContour(
                        contour=c,
                        object_id=obj_id,
                        shape_type=shape,
                        scale=scale,
                        variant_name=f"{obj_id}_var{variant}_n{noise}"
                    ))
                    sample_count += 1

        # Progress update every shape
        progress = (shape_idx + 1) / len(shape_types) * 100
        print(f"   ✅ {shape} complete ({sample_count:,}/{total_samples:,} samples, {progress:.1f}%)")

    print(f"✅ Dataset generation complete! Total: {len(dataset):,} samples")
    if vision_errors > 0:
        print(f"⚠️  Skipped {vision_errors} samples due to vision system errors (likely out of bounds)")
    if include_hard_negatives:
        print("🎯 Hard negative examples included for robust training!")
    if use_vision_simulation:
        print("🎥 All contours processed through vision system simulation!")
    return dataset
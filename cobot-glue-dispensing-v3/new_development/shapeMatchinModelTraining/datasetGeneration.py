import cv2
import numpy as np
import random
from dataclasses import dataclass
from shapeGenerator import generate_shape
# ======================================================
# 📊 Synthetic Contour Dataset Generation
# ======================================================

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

def generate_synthetic_dataset(n_shapes=8, n_scales=3, n_variants=5, n_noisy=4, include_hard_negatives=True):
    """
    Generate synthetic contour dataset with specified parameters
    
    Args:
        n_shapes: Number of different shape types to use
        n_scales: Number of different scales per shape
        n_variants: Number of rotation variants per scale
        n_noisy: Number of noise variants per rotation
        include_hard_negatives: Whether to ensure hard negative pairs are included
    
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
    
    dataset = []
    sample_count = 0

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
    if include_hard_negatives:
        print("🎯 Hard negative examples included for robust training!")
    return dataset
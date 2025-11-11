import os
import pickle
import json
import random
import itertools
from datetime import datetime
from datasetGeneration import SyntheticContour, generate_synthetic_dataset

# ======================================================
# 📊 Training Pairs Generation and Management
# ======================================================

def generate_balanced_pairs(dataset):
    """
    Create labeled pairs with truly balanced positive (same object) and negative (different object) samples.
    """
    print("🔄 Creating training pairs...")
    pairs_pos, pairs_neg = [], []
    grouped = {}

    # Group contours by object ID
    for s in dataset:
        grouped.setdefault(s.object_id, []).append(s)

    object_ids = list(grouped.keys())
    print(f"📊 Found {len(object_ids)} unique object types")

    # --- Positive pairs (same object ID) ---
    print("🔄 Generating positive pairs (same object)...")
    for obj_id, samples in grouped.items():
        for a, b in itertools.combinations(samples, 2):
            pairs_pos.append((a.contour, b.contour))
    print(f"   ✅ Generated {len(pairs_pos):,} positive pairs")

    # --- Negative pairs (different object IDs) ---
    print("🔄 Generating negative pairs (different objects)...")
    total_combinations = sum(len(grouped[object_ids[i]]) * len(grouped[object_ids[j]]) 
                           for i in range(len(object_ids)) 
                           for j in range(i + 1, len(object_ids)))
    
    pair_count = 0
    for i in range(len(object_ids)):
        for j in range(i + 1, len(object_ids)):
            samples_a = grouped[object_ids[i]]
            samples_b = grouped[object_ids[j]]
            # generate all combinations between objects i and j
            for a in samples_a:
                for b in samples_b:
                    pairs_neg.append((a.contour, b.contour))
                    pair_count += 1
        
        # Progress update every 10 object types
        if (i + 1) % 10 == 0:
            progress = pair_count / total_combinations * 100
            print(f"   📈 Progress: {pair_count:,}/{total_combinations:,} pairs ({progress:.1f}%)")
    
    print(f"   ✅ Generated {len(pairs_neg):,} negative pairs")

    # Downsample positives or negatives to match the smaller set
    print("🔄 Balancing dataset...")
    n = min(len(pairs_pos), len(pairs_neg))
    pairs_pos = random.sample(pairs_pos, n)
    pairs_neg = random.sample(pairs_neg, n)

    # Combine and create labels
    pairs = pairs_pos + pairs_neg
    labels = [1]*len(pairs_pos) + [0]*len(pairs_neg)

    # Shuffle
    print("🔄 Shuffling pairs...")
    combined = list(zip(pairs, labels))
    random.shuffle(combined)
    pairs, labels = zip(*combined)

    print(f"✅ Generated {len(pairs):,} truly balanced pairs ({len(pairs_pos):,} positive, {len(pairs_neg):,} negative)")
    return list(pairs), list(labels)

def save_pairs(pairs, labels, save_dir="saved_datasets", filename=None, n_curv_bins=16):
    """Save training pairs and labels to disk with comprehensive metadata in timestamped folder"""
    # Import here to avoid circular import
    from featuresExtraction import get_feature_extraction_metadata
    
    # Create timestamped folder for this dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_folder = os.path.join(save_dir, f"dataset_{timestamp}")
    os.makedirs(dataset_folder, exist_ok=True)
    
    # Create filename if not provided
    if filename is None:
        filename = f"training_pairs.pkl"
    
    filepath = os.path.join(dataset_folder, filename)
    
    # Get feature extraction metadata
    feature_metadata = get_feature_extraction_metadata(n_curv_bins)
    
    # Save pairs and labels with comprehensive metadata
    data = {
        'pairs': pairs,
        'labels': labels,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'dataset_id': f"dataset_{timestamp}",
        'total_pairs': len(pairs),
        'positive_pairs': sum(labels),
        'negative_pairs': len(labels) - sum(labels),
        'feature_extraction': feature_metadata,
        'dataset_info': {
            'curvature_bins': n_curv_bins,
            'expected_features_per_pair': feature_metadata['total_features'],
            'pair_generation_method': 'balanced_positive_negative',
            'hard_negatives_included': True  # Assuming hard negatives are included
        }
    }
    
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)
    
    # Save metadata as separate JSON file for easy viewing
    metadata_filepath = os.path.join(dataset_folder, "metadata.json")
    metadata_only = {k: v for k, v in data.items() if k not in ['pairs', 'labels']}
    with open(metadata_filepath, 'w') as f:
        json.dump(metadata_only, f, indent=2)
    
    # Save a summary file for quick reference
    summary_filepath = os.path.join(dataset_folder, "summary.txt")
    with open(summary_filepath, 'w') as f:
        f.write(f"Dataset Summary\n")
        f.write(f"===============\n")
        f.write(f"Created: {data['timestamp']}\n")
        f.write(f"Total pairs: {len(pairs):,}\n")
        f.write(f"Positive pairs: {sum(labels):,}\n")
        f.write(f"Negative pairs: {len(labels) - sum(labels):,}\n")
        f.write(f"Features per pair: {feature_metadata['total_features']}\n")
        f.write(f"Feature version: {feature_metadata['feature_extraction_version']}\n")
        f.write(f"Curvature bins: {n_curv_bins}\n")
    
    print(f"💾 Training pairs saved in folder: {dataset_folder}")
    print(f"📄 Files created:")
    print(f"   - {filename} (training pairs)")
    print(f"   - metadata.json (detailed metadata)")
    print(f"   - summary.txt (quick summary)")
    print(f"📊 Saved {len(pairs):,} pairs ({sum(labels):,} positive, {len(labels) - sum(labels):,} negative)")
    print(f"🔧 Features: {feature_metadata['total_features']} (version {feature_metadata['feature_extraction_version']})")
    
    return filepath, dataset_folder

def load_pairs(filepath):
    """Load training pairs and labels from disk"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Pairs file not found: {filepath}")
    
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    
    pairs = data['pairs']
    labels = data['labels']
    
    print(f"📂 Training pairs loaded: {filepath}")
    print(f"📊 Loaded {len(pairs):,} pairs ({sum(labels):,} positive, {len(labels) - sum(labels):,} negative)")
    print(f"🕒 Generated on: {data.get('timestamp', 'Unknown')}")
    
    return pairs, labels

def list_saved_pairs(save_dir="saved_datasets"):
    """List all saved training pair files"""
    if not os.path.exists(save_dir):
        print(f"No saved datasets directory found in {save_dir}.")
        return []
    
    pair_files = [f for f in os.listdir(save_dir) if f.endswith('.pkl')]
    pair_files.sort(reverse=True)  # Most recent first
    
    print(f"📋 Found {len(pair_files)} saved training datasets:")
    for i, filename in enumerate(pair_files, 1):
        filepath = os.path.join(save_dir, filename)
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            print(f"   {i}. {filename} - {data.get('total_pairs', 'Unknown')} pairs - {data.get('timestamp', 'Unknown')}")
        except:
            print(f"   {i}. {filename} - (corrupted or old format)")
    
    return pair_files

def get_or_generate_pairs(dataset, generate_new_pairs=True, pairs_file=None):
    """
    Get training pairs either by generating new ones or loading existing ones
    
    Args:
        dataset: The synthetic dataset (used only if generating new pairs)
        generate_new_pairs: If True, generate new pairs; if False, load existing ones
        pairs_file: Path to existing pairs file (required if generate_new_pairs=False)
    
    Returns:
        tuple: (pairs, labels)
    """
    if generate_new_pairs:
        print("🔄 Generating new training pairs...")
        pairs, labels = generate_balanced_pairs(dataset)
        
        # Save the generated pairs
        save_pairs(pairs, labels)
        
        return pairs, labels
    else:
        if pairs_file is None:
            # List available files and use the most recent one
            saved_files = list_saved_pairs()
            if not saved_files:
                raise ValueError("No saved training pairs found. Set generate_new_pairs=True to create new ones.")
            
            pairs_file = os.path.join("saved_datasets", saved_files[0])
            print(f"📂 Using most recent pairs file: {saved_files[0]}")
        
        print("📂 Loading existing training pairs...")
        return load_pairs(pairs_file)

def load_dataset_for_testing(n_shapes=22, n_scales=6, n_variants=6, n_noisy=6, include_hard_negatives=True):
    """
    Generate synthetic dataset for testing purposes
    
    Args:
        n_shapes: Number of different shape types to use
        n_scales: Number of different scales per shape
        n_variants: Number of rotation variants per scale
        n_noisy: Number of noise variants per rotation
        include_hard_negatives: Whether to ensure hard negative pairs are included
    
    Returns:
        List of SyntheticContour objects
    """
    print("🔄 Generating synthetic dataset for testing...")
    return generate_synthetic_dataset(
        n_shapes=n_shapes,
        n_scales=n_scales,
        n_variants=n_variants,
        n_noisy=n_noisy,
        include_hard_negatives=include_hard_negatives,
        use_vision_simulation=True,
        canvas_size=(1280, 720)
    )
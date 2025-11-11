import os
import json
import joblib
from datetime import datetime
from deprecated.contourMatching.shapeMatchinModelTraining.featuresExtraction import compute_enhanced_features

# ======================================================
# 💾 Model Persistence and Management
# ======================================================

def save_model(model, model_name, accuracy, save_dir="saved_models", dataset_info=None):
    """Save the trained model with comprehensive metadata in timestamped folder"""
    # Import here to avoid circular import
    from featuresExtraction import get_feature_extraction_metadata
    
    # Create timestamped folder for this model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_folder = os.path.join(save_dir, f"model_{timestamp}")
    os.makedirs(model_folder, exist_ok=True)
    
    # Create filename
    filename = f"{model_name.replace(' ', '_')}_acc{accuracy:.3f}.pkl"
    filepath = os.path.join(model_folder, filename)
    
    # Save model
    joblib.dump(model, filepath)
    
    # Get feature extraction metadata
    feature_metadata = get_feature_extraction_metadata()
    
    # Save comprehensive metadata
    metadata = {
        'model_info': {
            'model_id': f"model_{timestamp}",
            'model_name': model_name,
            'accuracy': accuracy,
            'timestamp': timestamp,
            'filename': filename,
            'training_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        'feature_extraction': feature_metadata,
        'dataset_info': dataset_info or {
            'source': 'unknown',
            'note': 'No dataset information provided'
        },
        'training_config': {
            'test_split': 0.3,
            'random_state': 42,
            'model_type': model_name
        },
        'compatibility': {
            'required_features': feature_metadata['total_features'],
            'feature_version': feature_metadata['feature_extraction_version'],
            'curvature_bins': feature_metadata['curvature_bins']
        }
    }
    
    # Save metadata
    metadata_file = os.path.join(model_folder, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save a summary file for quick reference
    summary_filepath = os.path.join(model_folder, "summary.txt")
    with open(summary_filepath, 'w') as f:
        f.write(f"Model Summary\n")
        f.write(f"=============\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Accuracy: {accuracy:.3f}\n")
        f.write(f"Trained: {metadata['model_info']['training_date']}\n")
        f.write(f"Features: {feature_metadata['total_features']} (version {feature_metadata['feature_extraction_version']})\n")
        f.write(f"Dataset: {dataset_info.get('pairs_file', 'unknown') if dataset_info else 'unknown'}\n")
        f.write(f"Training pairs: {dataset_info.get('total_training_pairs', 'unknown') if dataset_info else 'unknown'}\n")
    
    print(f"💾 Model saved in folder: {model_folder}")
    print(f"📄 Files created:")
    print(f"   - {filename} (trained model)")
    print(f"   - metadata.json (detailed metadata)")
    print(f"   - summary.txt (quick summary)")
    print(f"🔧 Compatible with {feature_metadata['total_features']} features (version {feature_metadata['feature_extraction_version']})")
    
    return filepath, model_folder

def load_model(filepath):
    """Load a saved model"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    model = joblib.load(filepath)
    print(f"📂 Model loaded: {filepath}")
    return model

def list_saved_models(save_dir="saved_models"):
    """List all saved models (supports both timestamped folders and direct files)"""
    if not os.path.exists(save_dir):
        print(f"No saved models directory found in {save_dir}.")
        return []
    
    model_info = []
    
    # First, look for timestamped model folders (new format)
    model_folders = [f for f in os.listdir(save_dir) 
                    if os.path.isdir(os.path.join(save_dir, f)) and f.startswith('model_')]
    
    for folder in model_folders:
        folder_path = os.path.join(save_dir, folder)
        # Find .pkl files in the folder
        pkl_files = [f for f in os.listdir(folder_path) if f.endswith('.pkl')]
        
        for pkl_file in pkl_files:
            model_path = os.path.join(folder_path, pkl_file)
            # Extract timestamp from folder name for sorting
            timestamp = folder.replace('model_', '')
            model_info.append({
                'path': model_path,
                'filename': pkl_file,
                'folder': folder,
                'timestamp': timestamp,
                'format': 'timestamped'
            })
    
    # Also look for direct .pkl files (old format) for backward compatibility
    direct_files = [f for f in os.listdir(save_dir) if f.endswith('.pkl')]
    for filename in direct_files:
        model_path = os.path.join(save_dir, filename)
        # Extract timestamp from filename if possible, otherwise use file modification time
        timestamp = str(int(os.path.getmtime(model_path)))
        model_info.append({
            'path': model_path,
            'filename': filename,
            'folder': None,
            'timestamp': timestamp,
            'format': 'direct'
        })
    
    # Sort by timestamp (most recent first)
    model_info.sort(key=lambda x: x['timestamp'], reverse=True)
    
    print(f"📋 Found {len(model_info)} saved models:")
    for i, info in enumerate(model_info, 1):
        if info['format'] == 'timestamped':
            print(f"   {i}. {info['filename']} (in {info['folder']})")
        else:
            print(f"   {i}. {info['filename']} (direct file)")
    
    return model_info

def get_latest_model(save_dir="saved_models"):
    """Get the path to the most recently saved model"""
    model_info = list_saved_models(save_dir)
    if not model_info:
        raise FileNotFoundError("No saved models found. Please run training first to create a model.")
    
    latest_info = model_info[0]  # Already sorted by timestamp (most recent first)
    filepath = latest_info['path']
    
    if latest_info['format'] == 'timestamped':
        print(f"📂 Latest model: {latest_info['filename']} (in {latest_info['folder']})")
    else:
        print(f"📂 Latest model: {latest_info['filename']} (direct file)")
    
    return filepath

def load_latest_model(save_dir="saved_models"):
    """Load the most recently saved model"""
    latest_path = get_latest_model(save_dir)
    return load_model(latest_path)

def predict_similarity(model, contour1, contour2):
    """Use trained model to predict similarity between two contours"""
    features = compute_enhanced_features(contour1, contour2)
    prediction = model.predict([features])[0]
    probability = model.predict_proba([features])[0]
    confidence = max(probability)
    print(f"🔍 Prediction: {'SAME' if prediction == 1 else 'DIFFERENT'} (Confidence: {confidence:.1%})")
    # # Filter by confidence

    # if prediction == 1: # SAME
    #     conf_low = 0.8
    #     conf_high = 0.95
    #
    #     if conf_low < confidence < conf_high:
    #         return "UNCERTAIN", confidence, features
    #     elif confidence < conf_low:
    #         return "DIFFERENT", confidence, features
    #     else:
    #         return "SAME", confidence, features
        
    result = "SAME" if prediction == 1 else "DIFFERENT"
    return result, confidence, features

def get_model_metadata(model_path):
    """Get metadata for a saved model (supports both timestamped folders and direct files)"""
    model_dir = os.path.dirname(model_path)
    model_filename = os.path.basename(model_path)
    
    # First, look for metadata.json in the same directory (new timestamped format)
    metadata_file = os.path.join(model_dir, "metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read metadata.json: {e}")
    
    # Fallback: try old filename-based metadata lookup
    try:
        # Filename format: ModelName_YYYYMMDD_HHMMSS_accX.XXX.pkl
        parts = model_filename.replace('.pkl', '').split('_')
        if len(parts) >= 3:
            timestamp_str = f"{parts[-3]}_{parts[-2]}"
            accuracy_str = parts[-1]
            
            # Look for corresponding metadata file (old format)
            old_metadata_file = os.path.join(model_dir, f"metadata_{timestamp_str}.json")
            if os.path.exists(old_metadata_file):
                with open(old_metadata_file, 'r') as f:
                    return json.load(f)
    except Exception:
        pass
    
    # Final fallback: extract basic info from filename
    return {
        'filename': model_filename,
        'timestamp': 'Unknown',
        'model_name': 'Unknown',
        'accuracy': 'Unknown',
        'note': 'No metadata file found'
    }

def delete_old_models(save_dir="saved_models", keep_latest=5):
    """Delete old models, keeping only the most recent ones (works with both folder and file structures)"""
    model_info = list_saved_models(save_dir)
    
    if len(model_info) <= keep_latest:
        print(f"📋 Only {len(model_info)} models found, nothing to delete")
        return
    
    models_to_delete = model_info[keep_latest:]
    deleted_count = 0
    
    for info in models_to_delete:
        try:
            if info['format'] == 'timestamped':
                # Delete entire folder
                import shutil
                folder_path = os.path.join(save_dir, info['folder'])
                shutil.rmtree(folder_path)
                print(f"   🗑️ Deleted folder: {info['folder']}")
            else:
                # Delete direct file
                os.remove(info['path'])
                print(f"   🗑️ Deleted file: {info['filename']}")
            
            deleted_count += 1
            
        except Exception as e:
            item_name = info['folder'] if info['format'] == 'timestamped' else info['filename']
            print(f"   ❌ Failed to delete {item_name}: {e}")
    
    print(f"🧹 Cleanup complete: deleted {deleted_count} old models, kept {keep_latest} latest")
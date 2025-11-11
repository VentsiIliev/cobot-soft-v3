import cv2
import numpy as np
import random
import itertools
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from scipy.spatial.distance import directed_hausdorff

import matplotlib.pyplot as plt
from dataclasses import dataclass

# ======================================================
# 1️⃣ Synthetic Contour Dataset Generation (with noise)
# ======================================================

@dataclass
class SyntheticContour:
    contour: np.ndarray
    object_id: str
    shape_type: str
    scale: float
    variant_name: str

def generate_shape(shape_type, scale=1.0, img_size=(256, 256)):
    img = np.zeros(img_size, dtype=np.uint8)
    h, w = img_size
    cx, cy = w // 2, h // 2
    base = int(50 * scale)

    if shape_type == "circle":
        cv2.circle(img, (cx, cy), base, 255, -1)
    elif shape_type == "ellipse":
        cv2.ellipse(img, (cx, cy), (base, int(base * 0.6)), 0, 0, 360, 255, -1)
    elif shape_type == "rectangle":
        cv2.rectangle(img, (cx - base, cy - base), (cx + base, cy + base), 255, -1)
    elif shape_type == "triangle":
        pts = np.array([[cx, cy - base], [cx - base, cy + base], [cx + base, cy + base]])
        cv2.drawContours(img, [pts], 0, 255, -1)
    elif shape_type == "polygon":
        pts = np.array([
            [cx + int(base * np.cos(a)), cy + int(base * np.sin(a))]
            for a in np.linspace(0, 2*np.pi, random.randint(5, 8), endpoint=False)
        ], np.int32)
        cv2.drawContours(img, [pts], 0, 255, -1)
    elif shape_type == "star":
        pts = []
        for i in range(5):
            outer = base
            inner = base // 2
            angle = i * (2 * np.pi / 5)
            pts.append([cx + int(outer * np.cos(angle)), cy + int(outer * np.sin(angle))])
            pts.append([cx + int(inner * np.cos(angle + np.pi / 5)), cy + int(inner * np.sin(angle + np.pi / 5))])
        pts = np.array(pts)
        cv2.drawContours(img, [pts], 0, 255, -1)

    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(contours, key=cv2.contourArea)

def rotate_contour(contour, angle_deg):
    pts = contour.reshape(-1, 2)
    cx, cy = np.mean(pts, axis=0)
    rad = np.deg2rad(angle_deg)
    rot = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
    rotated = np.dot(pts - [cx, cy], rot.T) + [cx, cy]
    return rotated.reshape(-1, 1, 2).astype(np.float32)

def jitter_contour(contour, noise_level=0.5):
    pts = contour.reshape(-1, 2)
    noise = np.random.normal(scale=noise_level, size=pts.shape)
    return (pts + noise).reshape(-1, 1, 2).astype(np.float32)

def deform_contour(contour, deform_strength=0.03):
    pts = contour.reshape(-1, 2)
    for i in range(len(pts)):
        pts[i] += np.random.randn(2) * deform_strength * 100
    return pts.reshape(-1, 1, 2).astype(np.float32)

def simplify_contour(contour, epsilon_ratio=0.01):
    epsilon = epsilon_ratio * cv2.arcLength(contour, True)
    return cv2.approxPolyDP(contour, epsilon, True)

def generate_synthetic_dataset(n_shapes=4, n_scales=3, n_variants=5, n_noisy=4):
    shape_types = random.sample(["circle", "ellipse", "rectangle", "triangle", "polygon", "star"], n_shapes)
    dataset = []

    for shape in shape_types:
        for scale_idx in range(n_scales):
            scale = 0.5 + scale_idx * 0.3
            base = generate_shape(shape, scale)
            obj_id = f"{shape}_scale{scale_idx}"

            for variant in range(n_variants):
                rot = rotate_contour(base, random.uniform(0, 360))
                for noise in range(n_noisy):
                    c = jitter_contour(rot, 0.5)
                    c = deform_contour(c, 0.03)
                    c = simplify_contour(c)
                    dataset.append(SyntheticContour(
                        contour=c,
                        object_id=obj_id,
                        shape_type=shape,
                        scale=scale,
                        variant_name=f"{obj_id}_var{variant}_n{noise}"
                    ))
    return dataset

# ======================================================
# 2️⃣ Feature Extraction Between Two Contours
# ======================================================

def convexity_ratio(contour):
    hull = cv2.convexHull(contour)
    if cv2.contourArea(hull) == 0: return 0
    return cv2.contourArea(contour) / cv2.contourArea(hull)

def hausdorff_distance(c1, c2):
    """Compute simple Hausdorff distance manually."""
    pts1 = c1.reshape(-1, 2)
    pts2 = c2.reshape(-1, 2)
    return max(
        directed_hausdorff(pts1, pts2)[0],
        directed_hausdorff(pts2, pts1)[0]
    )

def compute_features(c1, c2):
    m = cv2.matchShapes(c1, c2, cv2.CONTOURS_MATCH_I1, 0.0)
    conv = abs(convexity_ratio(c1) - convexity_ratio(c2))

    # fallback simple Hausdorff instead of shape context
    sc = hausdorff_distance(c1, c2)
    return [m, conv, sc]

# ======================================================
# 3️⃣ Dataset → Training Pairs
# ======================================================

def generate_pairs(dataset):
    pairs, labels = [], []
    grouped = {}

    for s in dataset:
        grouped.setdefault(s.object_id, []).append(s)

    ids = list(grouped.keys())

    for obj_id, samples in grouped.items():
        for a, b in itertools.combinations(samples, 2):
            pairs.append((a.contour, b.contour))
            labels.append(1)

    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = random.choice(grouped[ids[i]])
            b = random.choice(grouped[ids[j]])
            pairs.append((a.contour, b.contour))
            labels.append(0)

    print(f"✅ Generated {len(pairs)} pairs ({sum(labels)} positive, {len(labels) - sum(labels)} negative)")
    return pairs, labels

# ======================================================
# 4️⃣ Train the Model to Learn Optimal Weights
# ======================================================

def train_similarity_model(pairs, labels):
    X = [compute_features(a, b) for a, b in pairs]
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = LogisticRegression()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)

    print("✅ Training complete.")
    print(f"Accuracy: {acc:.3f}")
    print("Weights learned:", model.coef_)

    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["Different", "Same"]))

    return model, X_test, y_test, preds

# ======================================================
# 5️⃣ Example Run
# ======================================================

if __name__ == "__main__":
    dataset = generate_synthetic_dataset()
    pairs, labels = generate_pairs(dataset)
    model, X_test, y_test, preds = train_similarity_model(pairs, labels)

    # Optional: visualize performance
    cm = confusion_matrix(y_test, preds)
    plt.imshow(cm, cmap="Blues")
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.show()

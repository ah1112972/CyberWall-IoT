# train_model_full_v2.py
# Purpose: Same as train_model_full.py, but with SOFTENED class weights
# (square root instead of raw ratio) to reduce the false-alarm overcorrection
# we discovered during evaluation — while still prioritizing rare classes
# more than common ones.

import pandas as pd
import math  # gives us access to math.sqrt()
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

from label_mapping import add_category_column

print("Loading train.csv into memory...")
df = pd.read_csv("data/raw/train.csv")
df = add_category_column(df)
print(f"Loaded {len(df)} rows.")

NON_FEATURE_COLS = ["label", "category"]
X = df.drop(columns=NON_FEATURE_COLS)
y = df["category"]

# --- Compute REAL class weights from the actual training data ---
# Instead of hardcoding counts from validation.csv like before, we now
# calculate them directly from the full train.csv, since we've already
# loaded it all into memory anyway. More accurate than our earlier estimate.
category_counts = y.value_counts().to_dict()
# .value_counts() = counts each unique value, like before.
# .to_dict() converts the result into a plain dictionary: {"DDoS": 3982483, ...}

total_samples = len(y)
n_classes = len(category_counts)

# --- Step 1: compute the RAW balanced weight, same formula as before ---
raw_weights = {
    cls: total_samples / (n_classes * count) for cls, count in category_counts.items()
}

# --- Step 2: soften each weight by taking its square root ---
# Why square root specifically? It shrinks large numbers MUCH more than
# small numbers, proportionally. Example: sqrt(2984) ≈ 54.6 — the gap
# between a weight of 0.17 and 507 (a ~2984x difference) becomes a gap
# between roughly 0.4 and 22.5 (still meaningful, but far less extreme).
# This is a common, simple technique for "de-fanging" an overly aggressive
# balancing formula without abandoning the idea entirely.
softened_weights = {cls: math.sqrt(w) for cls, w in raw_weights.items()}

print("Raw (unsoftened) weights:", raw_weights)
print("Softened (sqrt) weights:", softened_weights)

# --- Scale features ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- Train using the SOFTENED weights instead of raw balanced weights ---
model = SGDClassifier(
    loss="log_loss",
    class_weight=softened_weights,  # <-- the only real change from before
    random_state=42,
)

print("Training on full dataset with softened weights...")
model.fit(X_scaled, y)
print("Training complete.")

# --- Save to a NEW folder, so we don't overwrite our original results ---
# Keeping both versions lets us directly compare "raw weights vs softened
# weights" in your FYP report as an experiment, not just a fix.
os.makedirs("ml/checkpoints_v2", exist_ok=True)
joblib.dump(model, "ml/checkpoints_v2/sgd_model_v2.joblib")
joblib.dump(scaler, "ml/checkpoints_v2/scaler_v2.joblib")
print("Model and scaler saved to ml/checkpoints_v2/")
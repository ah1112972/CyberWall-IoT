# train_model_full.py
# Purpose: Train an SGDClassifier on the ENTIRE train.csv at once, without
# chunking. This is the "traditional" approach — simpler code, but requires
# loading the whole dataset into RAM in one go, and no ability to pause
# partway through and resume later like train_model.py does.

import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Reuse the same confirmed label mapping from before — no need to rewrite it
from label_mapping import add_category_column

# --- Load the ENTIRE file into memory at once ---

print("Loading train.csv into memory — this may take a while...")
df = pd.read_csv("data/raw/train.csv")
print(f"Loaded {len(df)} rows.")

# --- Apply our label -> category mapping to the whole dataset at once ---
df = add_category_column(df)

# --- Split into features (X) and target (y) ---
NON_FEATURE_COLS = ["label", "category"]
X = df.drop(columns=NON_FEATURE_COLS)
y = df["category"]

# --- Scale all features at once ---

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- Create and train the model in ONE call ---
# class_weight="balanced" is passed as the STRING here (not a manually
# computed dictionary like in train_model.py). This works safely now
# because .fit() sees the ENTIRE dataset's class distribution at once,
# so Scikit-learn can compute accurate balanced weights itself — no risk
# of a single chunk having a skewed/incomplete view of the class counts.
model = SGDClassifier(loss="log_loss", class_weight="balanced", random_state=42)

# --- The actual training step ---
# Regular .fit() (not partial_fit) — trains on all the data in one call.
# There is no loop here, no chunks, no resuming — it either finishes or
# it doesn't, in this single run.
print("Training on full dataset...")
model.fit(X_scaled, y)
print("Training complete.")

# --- Save the final model and scaler ---
# Still worth saving to disk so we don't have to retrain from scratch
# every time we want to evaluate or use this model.
os.makedirs("ml/checkpoints_full", exist_ok=True)
joblib.dump(model, "ml/checkpoints_full/sgd_model_full.joblib")
joblib.dump(scaler, "ml/checkpoints_full/scaler_full.joblib")
print("Model and scaler saved to ml/checkpoints_full/")
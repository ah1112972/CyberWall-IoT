# threshold_demo.py
# Purpose: Demonstrate confidence-threshold based prediction, matching
# FR-11 in our SRS ("trigger a block action... above a configurable
# confidence threshold") — instead of blindly accepting the model's
# single top guess no matter how uncertain it was.

import pandas as pd
import joblib
import numpy as np

from label_mapping import add_category_column

df = pd.read_csv("data/raw/test.csv")
df = add_category_column(df)

NON_FEATURE_COLS = ["label", "category"]
X_test = df.drop(columns=NON_FEATURE_COLS)
y_test = df["category"]

model = joblib.load("ml/checkpoints_v2/sgd_model_v2.joblib")
scaler = joblib.load("ml/checkpoints_v2/scaler_v2.joblib")
X_test_scaled = scaler.transform(X_test)

# --- predict_proba() instead of predict() ---
# predict() gives you ONE label per row (the model's best guess).
# predict_proba() instead gives you a full probability distribution across
# ALL 8 classes for every row — e.g. [0.05, 0.02, 0.80, 0.01, 0.03, 0.04, 0.03, 0.02]
# meaning "80% confident this is class index 2" and so on.
probabilities = model.predict_proba(X_test_scaled)

# model.classes_ tells us WHICH column corresponds to which category name,
# since predict_proba() just returns raw numbers in a fixed column order —
# we need this to know column 2 means "DDoS" and not something else.
class_names = model.classes_
print("Class order:", class_names)

# --- For each row, find the highest probability AND which class it belongs to ---
# np.argmax finds the INDEX of the largest value in each row (like finding
# the position of the biggest element in an array, not the value itself).
best_class_index = np.argmax(probabilities, axis=1)  # axis=1 = per row, not per column
confidence = np.max(probabilities, axis=1)  # the actual highest probability value

predicted_labels = class_names[best_class_index]  # convert index -> actual class name

# --- Apply a confidence threshold ---
# Only "trust" a prediction if the model was at least this confident.
# Anything below this gets marked as "Uncertain" instead of forcing a guess —
# in a real IDS/IPS, this could mean "flag for human review" instead of
# "auto-block," directly matching your FR-11/FR-12 requirements.
THRESHOLD = 0.70

final_predictions = np.where(confidence >= THRESHOLD, predicted_labels, "Uncertain")

# --- Quick check: how many predictions were confident vs uncertain? ---
uncertain_count = (final_predictions == "Uncertain").sum()
print(f"\nOut of {len(final_predictions)} predictions, {uncertain_count} fell below "
      f"the {THRESHOLD} confidence threshold and were marked Uncertain.")

# --- Specifically check BruteForce: how many were confidently flagged? ---
brute_force_confident = ((final_predictions == "BruteForce")).sum()
print(f"Rows confidently classified as BruteForce (>= {THRESHOLD} confidence): {brute_force_confident}")
print("(Compare this to the 24,403 raw predictions from before the threshold was applied.)")
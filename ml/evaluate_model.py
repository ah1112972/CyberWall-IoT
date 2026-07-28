# evaluate_model.py
# Purpose: Evaluate the final Random Forest model against BOTH test.csv
# and validation.csv, to check the model generalizes consistently rather
# than performing well on just one specific file.

import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix

from label_mapping import add_category_column

NON_FEATURE_COLS = ["label", "category"]


def load_and_prepare(csv_path):
    """
    Loads a CSV, applies our label->category mapping, and splits it into
    X (features) and y (target). Written as a function so we can reuse
    the exact same steps for test.csv AND validation.csv without repeating
    code — reduces the risk of accidentally treating one file differently.
    """
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    df = add_category_column(df)
    X = df.drop(columns=NON_FEATURE_COLS)
    y = df["category"]
    print(f"Loaded {len(df)} rows from {csv_path}.\n")
    return X, y


def evaluate(model_path, scaler_path, model_name, X, y):
    """
    Now takes X and y as explicit parameters instead of relying on
    global variables — this is what lets us call this SAME function
    against test.csv's data in one call, and validation.csv's data in
    another, just by passing different arguments.
    """
    print(f"{'=' * 60}")
    print(f"Evaluating: {model_name}")
    print(f"{'=' * 60}")

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)

    print("\nClassification Report:")
    print(classification_report(y, y_pred, zero_division=0))

    labels = sorted(y.unique())
    cm = confusion_matrix(y, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print("\nConfusion Matrix (rows=actual, columns=predicted):")
    print(cm_df)
    print()


# --- Load both datasets once, upfront ---
X_test, y_test = load_and_prepare("data/raw/test.csv")
X_val, y_val = load_and_prepare("data/raw/validation.csv")

# --- Evaluate the final Random Forest model against BOTH files ---
evaluate(
    "ml/checkpoints_rf/rf_model.joblib",
    "ml/checkpoints_rf/scaler_rf.joblib",
    "Random Forest — on TEST set",
    X_test, y_test,
)

evaluate(
    "ml/checkpoints_rf/rf_model.joblib",
    "ml/checkpoints_rf/scaler_rf.joblib",
    "Random Forest — on VALIDATION set",
    X_val, y_val,
)
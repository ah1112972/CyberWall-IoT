# evaluate_model.py
# Purpose: Load test.csv (data neither model has ever seen), run both our
# trained models against it, and report per-class precision/recall/F1 plus
# a confusion matrix, so we know how good the models ACTUALLY are — not
# just their overall accuracy, which can hide poor performance on rare classes.

import pandas as pd
import joblib  # to load our saved model/scaler files back into memory
from sklearn.metrics import classification_report, confusion_matrix

from label_mapping import add_category_column

# --- Load the test set (never used in training — this is the real test) ---
print("Loading test.csv...")
df = pd.read_csv("data/raw/test.csv")
df = add_category_column(df)

NON_FEATURE_COLS = ["label", "category"]
X_test = df.drop(columns=NON_FEATURE_COLS)
y_test = df["category"]

print(f"Loaded {len(df)} test rows.\n")


def evaluate(model_path, scaler_path, model_name):
    """
    Loads one trained model + its scaler, runs predictions on the test set,
    and prints a full evaluation report. Written as a function so we can
    call it twice (once per model) without duplicating code.
    """
    print(f"{'=' * 60}")
    print(f"Evaluating: {model_name}")
    print(f"{'=' * 60}")

    # Load the saved model and scaler back from disk (reverse of joblib.dump)
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # IMPORTANT: we must use the SAME scaler that was fit during training
    # (.transform(), not .fit_transform()) — otherwise we'd be rescaling
    # test data using test data's own statistics, which would be invalid
    # and not reflect real-world deployment (where new traffic must be
    # scaled using parameters learned from training data only).
    X_test_scaled = scaler.transform(X_test)

    # Ask the model to predict a category for every row in the test set
    y_pred = model.predict(X_test_scaled)

    # --- Per-class precision, recall, F1-score ---
    # zero_division=0 tells sklearn to report 0 (instead of crashing with a
    # warning) for any class the model never predicted at all — which is a
    # real possibility for our rarest classes like BruteForce.
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # --- Confusion matrix ---
    # Rows = actual category, Columns = predicted category.
    # Reading it: matrix[i][j] = how many rows of TRUE category i got
    # PREDICTED as category j. The diagonal = correct predictions;
    # everything off-diagonal = mistakes, and WHICH mistake was made.
    labels = sorted(y_test.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print("\nConfusion Matrix (rows=actual, columns=predicted):")
    print(cm_df)

    print()  # blank line for readability between the two model reports


# # --- Evaluate the chunked model ---
# evaluate(
#     "ml/checkpoints/sgd_model.joblib",
#     "ml/checkpoints/scaler.joblib",
#     "Chunked model (partial_fit, 55 chunks)",
# )

# # --- Evaluate the full-batch model ---
# evaluate(
#     "ml/checkpoints_full/sgd_model_full.joblib",
#     "ml/checkpoints_full/scaler_full.joblib",
#     "Full-batch model (fit on all rows at once)",
# )

evaluate(
    "ml/checkpoints_rf/rf_model.joblib",
    "ml/checkpoints_rf/scaler_rf.joblib",
    "Random Forest (RobustScaler, balanced_subsample)",
)
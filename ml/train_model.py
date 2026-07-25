# train_model.py
# Purpose: Train an SGDClassifier on CICIoT2023 in daily chunks, using
# partial_fit() so we never need the full 1.6GB train.csv in memory at once,


import pandas as pd
import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
import joblib  # used to save/load model + scaler state to disk between sessions
import os


from label_mapping import label_to_category, add_category_column


CLASSES = np.array(["Benign", "DDoS", "DoS", "Mirai", "Recon", "Spoofing", "Web", "BruteForce"])





category_counts = {
    "DDoS": 857523, "DoS": 203450, "Mirai": 66091, "Benign": 27519,
    "Spoofing": 12306, "Recon": 9015, "Web": 657, "BruteForce": 290,
}
total_samples = sum(category_counts.values())
n_classes = len(category_counts)
class_weight_dict = {
    cls: total_samples / (n_classes * count) for cls, count in category_counts.items()
}
print("Computed class weights:", class_weight_dict)

# --- File paths for saving/resuming progress ---
MODEL_PATH = "ml/checkpoints/sgd_model.joblib"
SCALER_PATH = "ml/checkpoints/scaler.joblib"
PROGRESS_PATH = "ml/checkpoints/progress.txt"  # tracks which chunk we're on

os.makedirs("ml/checkpoints", exist_ok=True)

# --- Columns to drop before training ---

NON_FEATURE_COLS = ["label", "category"]

CHUNK_SIZE = 100_000  # rows per chunk; ~100k rows keeps memory low per step


def load_or_create_model():
    
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        print("Found existing checkpoint — resuming from saved progress.")
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
    else:
        print("No checkpoint found — starting fresh.")
        # loss='log_loss' lets us later get probability scores, not just hard labels
        model = SGDClassifier(loss="log_loss", class_weight=class_weight_dict, random_state=42)
        scaler = StandardScaler()
    return model, scaler


def load_progress():
    """Returns how many chunks we've already processed (0 if starting fresh)."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            return int(f.read().strip())
    return 0


def save_progress(chunk_number):
    with open(PROGRESS_PATH, "w") as f:
        f.write(str(chunk_number))


def main():
    model, scaler = load_or_create_model()
    chunks_already_done = load_progress()
    print(f"Chunks already completed: {chunks_already_done}")

    # pd.read_csv with chunksize returns an iterator, NOT the whole file —
    # each loop iteration only loads CHUNK_SIZE rows into memory at a time.
    chunk_reader = pd.read_csv("data/raw/train.csv", chunksize=CHUNK_SIZE)

    for i, chunk in enumerate(chunk_reader):
        # Skip chunks we've already trained on in previous days
        if i < chunks_already_done:
            continue

        # Apply our confirmed label -> category mapping to this chunk
        chunk = add_category_column(chunk)

        # Separate features (X) from target labels (y)
        X = chunk.drop(columns=NON_FEATURE_COLS)
        y = chunk["category"]

        # --- Scale features incrementally ---
        # StandardScaler has partial_fit too, so it learns mean/variance
        # gradually across chunks, same as the classifier does.
        scaler.partial_fit(X)
        X_scaled = scaler.transform(X)

        # --- Train on this chunk ---
        # classes=CLASSES is REQUIRED on every call for SGDClassifier's
        # partial_fit, so it always knows the full set of possible labels,
        # even in chunks that don't happen to contain a rare class like BruteForce.
        model.partial_fit(X_scaled, y, classes=CLASSES)

        print(f"Chunk {i + 1} done — trained on {len(chunk)} rows.")

        # --- Save progress after EVERY chunk ---
        # This is what lets us stop after 15-20 minutes today and resume
        # tomorrow without losing any learned progress.
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        save_progress(i + 1)

        # --- Daily stopping point ---
        # Stop after a fixed number of chunks per session so this fits
        # inside a reasonable daily time budget instead of running for hours.
        CHUNKS_PER_DAY = 1000   # 5 chunks x 100k rows = 500k rows per day
        if (i + 1) - chunks_already_done >= CHUNKS_PER_DAY:
            print(f"\nStopping for today after {CHUNKS_PER_DAY} chunks. Run again tomorrow to continue.")
            break


if __name__ == "__main__":
    main()
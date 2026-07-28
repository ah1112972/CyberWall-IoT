# train_model_rf.py
# Purpose: Train a Random Forest classifier with RobustScaler, as an
# alternative to our linear SGDClassifier — testing whether a non-linear
# model handles the DoS/DDoS overlap and outlier-heavy features better.

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import RobustScaler  # <-- new, instead of StandardScaler
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

# --- RobustScaler instead of StandardScaler ---
# StandardScaler: (value - mean) / standard_deviation
#   -> a single extreme outlier (like that Header_Length of 2,345,336 we
#      saw during exploration) drags the mean far from where most data
#      actually sits, distorting the scaling for EVERY row.
# RobustScaler: (value - median) / IQR (interquartile range)
#   -> median and IQR are calculated from the MIDDLE 50% of the data,
#      so a handful of extreme outliers barely affect the result at all.
#      Same overall idea (put all features on a comparable scale),
#      just using statistics that resist being thrown off by outliers.
scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

# --- Random Forest ---
# n_estimators=100: build 100 individual decision trees. Each tree sees a
#   slightly different random subset of rows and features (this randomness
#   is WHY it's called a "forest" of trees rather than one single tree).
#   The forest's final prediction = majority vote across all 100 trees.
# max_depth=20: caps how many yes/no questions deep a single tree can go
#   before making a decision. Without a cap, trees can grow until every
#   leaf has just 1-2 rows — memorizing noise instead of learning general
#   patterns (overfitting). 20 is a reasonable starting cap, not a magic number.
# class_weight='balanced_subsample': similar idea to what we did manually
#   for SGD, but recalculated fresh for each individual tree's random data
#   subset, rather than one fixed set of weights for the whole forest.
#   Often works better for Random Forest specifically than a single
#   precomputed weight dictionary.
# n_jobs=-1: use ALL available CPU cores to build trees in parallel
#   (-1 means "use every core available"), since trees don't depend on
#   each other the way SGD's sequential chunk-by-chunk updates do.
# verbose=1: print progress messages so we can see it's actually working,
#   rather than sitting silently for a long time like our first full-batch run.
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    class_weight="balanced_subsample",
    n_jobs=-1,
    random_state=42,
    verbose=1,
)

print("Training Random Forest on full dataset...")
model.fit(X_scaled, y)
print("Training complete.")

os.makedirs("ml/checkpoints_rf", exist_ok=True)
joblib.dump(model, "ml/checkpoints_rf/rf_model.joblib")
joblib.dump(scaler, "ml/checkpoints_rf/scaler_rf.joblib")
print("Model and scaler saved to ml/checkpoints_rf/")
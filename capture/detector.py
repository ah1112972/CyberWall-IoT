# capture/detector.py
# Purpose: Takes a completed flow's features, runs them through our
# trained Random Forest model, and returns a prediction + confidence.

import joblib
import pandas as pd

# This list MUST match the exact order of columns the model was trained
# on (same order as the original CICIoT2023 CSV, minus the label column).
# If this order is wrong, the model will silently give garbage predictions
# — it has no idea what a column "means," only its position.
FEATURE_ORDER = [
    "flow_duration", "Header_Length", "Protocol Type", "Duration", "Rate",
    "Srate", "Drate", "fin_flag_number", "syn_flag_number", "rst_flag_number",
    "psh_flag_number", "ack_flag_number", "ece_flag_number", "cwr_flag_number",
    "ack_count", "syn_count", "fin_count", "urg_count", "rst_count",
    "HTTP", "HTTPS", "DNS", "Telnet", "SMTP", "SSH", "IRC", "TCP", "UDP",
    "DHCP", "ARP", "ICMP", "IPv", "LLC", "Tot sum", "Min", "Max", "AVG",
    "Std", "Tot size", "IAT", "Number", "Magnitue", "Radius", "Covariance",
    "Variance", "Weight",
]


class Detector:
    """
    Wraps our trained model + scaler, and exposes one simple method:
    give it a feature dictionary, get back a category and confidence.
    """

    def __init__(self, model_path, scaler_path):
        print("Loading trained model and scaler...")
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        print("Model loaded successfully.")

    def predict(self, features: dict):
        """
        features: the dictionary produced by Flow.compute_features()
        Returns: (predicted_category: str, confidence: float)
        """
        # Build a single-row table with columns in the EXACT order the
        # model expects, pulling each value out of our features dict
        # by name so we never rely on dictionary ordering by accident.
        row = [[features[col] for col in FEATURE_ORDER]]
        X = pd.DataFrame(row, columns=FEATURE_ORDER)

        # Apply the SAME scaling the model was trained with — using
        # .transform(), not .fit_transform(), since we must reuse the
        # statistics learned during training, not recalculate new ones
        # from this single live sample.
        X_scaled = self.scaler.transform(X)

        # predict_proba gives us confidence scores for ALL 8 categories,
        # not just the single best guess — this is what lets us apply
        # a confidence threshold (FR-11) instead of blindly trusting
        # whatever the top guess happens to be.
        probabilities = self.model.predict_proba(X_scaled)[0]
        class_names = self.model.classes_

        best_index = probabilities.argmax()
        predicted_category = class_names[best_index]
        confidence = probabilities[best_index]

        return predicted_category, float(confidence)
import pandas as pd

df = pd.read_csv("data/raw/validation.csv")


# --- Basic shape check ---
print("Shape (rows, columns):", df.shape)


# --- Column names ---
print("\nColumn names:")
print(df.columns.tolist())


# --- Data types per column ---
print("\nData types:")
print(df.dtypes)


# --- Memory usage ---
mem_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
print(f"\nMemory usage: {mem_mb:.2f} MB")


# --- First few rows ---
print("\nFirst 5 rows:")
print(df.head())


# --- Try to auto-detect the label/attack-type column ---
# possible_label_cols = [col for col in df.columns if "label" in col.lower() or "type" in col.lower() or "attack" in col.lower()]
# print("\nPossible label columns found:", possible_label_cols)

label_col = "label"
print(f"\nClass distribution for '{label_col}':")
print(df[label_col].value_counts())

# --- Class distribution as percentages ---
print(f"\nClass distribution for '{label_col}' (percentages):")
print((df[label_col].value_counts(normalize=True) * 100).round(2))


# --- Number of distinct classes ---
print(f"\nNumber of distinct classes: {df[label_col].nunique()}")


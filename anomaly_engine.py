import pandas as pd


# ==============================
# CONFIG
# ==============================

# Only these keywords are considered medical signals
MEDICAL_KEYWORDS = [
    "weight",
    "height",
    "heart",
    "pulse",
    "spo2",
    "o2",
    "oxygen",
    "bp",
    "pressure",
    "systolic",
    "diastolic",
    "glucose",
    "sugar",
    "temperature",
    "temp",
    "bmi",
    "respiration",
    "respiratory",
    "rate"
]

# Percentile thresholds
LOWER_Q = 0.05
UPPER_Q = 0.95

MIN_ROWS = 10


# ==============================
# HELPERS
# ==============================
def is_medical_column(col_name: str) -> bool:
    col = col_name.lower()
    return any(keyword in col for keyword in MEDICAL_KEYWORDS)


def is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


# ==============================
# MEDICAL ANOMALY DETECTOR
# ==============================
def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    anomalies = []

    # -----------------------------
    # Select medical numeric columns
    # -----------------------------
    candidate_cols = []

    for col in df.columns:
        if not is_medical_column(col):
            continue

        numeric_series = pd.to_numeric(df[col], errors="coerce")

        if numeric_series.notna().sum() >= MIN_ROWS:
            df[col] = numeric_series
            candidate_cols.append(col)

    if not candidate_cols:
        return pd.DataFrame()

    # -----------------------------
    # Detect anomalies per column
    # -----------------------------
    for col in candidate_cols:
        values = df[col].dropna()

        if len(values) < MIN_ROWS:
            continue

        low = values.quantile(LOWER_Q)
        high = values.quantile(UPPER_Q)

        for idx, value in df[col].items():
            if pd.isna(value):
                continue

            if value < low or value > high:
                anomalies.append({
                    "Row Index": idx,
                    "Medical Field": col,
                    "Observed Value": value,
                    "Expected Range": f"{round(low,2)} – {round(high,2)}",
                    "Reason": f"{col} outside normal learned medical range"
                })

    return pd.DataFrame(anomalies)

import pandas as pd
from datetime import timedelta

# ==============================
# FILTER VALID COLUMNS
# ==============================
def get_valid_columns(df):
    valid_cols = []
    for col in df.columns:
        if col is None:
            continue
        if str(col).strip() == "":
            continue
        if str(col).lower().startswith("unnamed"):
            continue

        non_empty = df[col].astype(str).str.strip().ne("").any()
        if non_empty:
            valid_cols.append(col)

    return valid_cols

# ==============================
# CHECK DATE COLUMN (SAFE)
# ==============================
def is_date_column(series):
    parsed = pd.to_datetime(series, errors="coerce")
    valid_ratio = parsed.notna().mean()

    # If at least 70% values look like dates, treat as date column
    return valid_ratio >= 0.7


# ==============================
# FIND DATE GAPS
# ==============================
def find_date_gaps(series):
    parsed = pd.to_datetime(series, errors="coerce")
    dates = parsed.dropna().sort_values().unique()

    gaps = []
    for i in range(len(dates) - 1):
        if (dates[i + 1] - dates[i]).days > 1:
            gaps.append(
                f"No records found between "
                f"{(dates[i] + timedelta(days=1)).strftime('%d %b %Y')} and "
                f"{(dates[i + 1] - timedelta(days=1)).strftime('%d %b %Y')}"
            )
    return gaps

# ==============================
# FORMAT DURATION
# ==============================
def format_duration(td):
    if pd.isna(td):
        return None

    total_minutes = int(td.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0 and minutes > 0:
        return f"{hours} hr {minutes} min"
    elif hours > 0:
        return f"{hours} hr"
    else:
        return f"{minutes} min"

# ==============================
# DETECT LOGIN / LOGOUT COLUMNS
# ==============================
def detect_login_logout_columns(df):
    login_keywords = ["login", "checkin", "in time", "entry", "start"]
    logout_keywords = ["logout", "checkout", "out time", "exit", "end"]

    login_col = None
    logout_col = None

    for col in df.columns:
        col_l = col.lower()
        if any(k in col_l for k in login_keywords):
            login_col = col
        if any(k in col_l for k in logout_keywords):
            logout_col = col

    return login_col, logout_col

# ==============================
# ADD DURATION (NON-DESTRUCTIVE)
# ==============================
def add_duration_column(df, login_col, logout_col):
    df = df.copy()

    login_parsed = pd.to_datetime(df[login_col], errors="coerce")
    logout_parsed = pd.to_datetime(df[logout_col], errors="coerce")

    duration_td = logout_parsed - login_parsed
    df["Duration"] = duration_td.apply(format_duration)

    return df

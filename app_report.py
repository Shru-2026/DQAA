import streamlit as st
import pandas as pd
from datetime import timedelta

# ==============================
# LOAD FILE
# ==============================
def load_data(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file format")
        return None

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

        # At least one non-empty value
        non_empty = df[col].astype(str).str.strip().ne("").any()
        if non_empty:
            valid_cols.append(col)

    return valid_cols

# ==============================
# CHECK DATE COLUMN (SAFE)
# ==============================
def is_date_column(series):
    try:
        pd.to_datetime(series.dropna().iloc[:10], errors="raise")
        return True
    except:
        return False

# ==============================
# FIND DATE GAPS (ANALYTICS ONLY)
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

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="Hospital Data Quality Report", layout="wide")
st.title("🏥 Hospital Data Quality Assessment Report")

uploaded_file = st.file_uploader(
    "Upload Hospital Data (CSV / Excel)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    df = load_data(uploaded_file)

    if df is not None:
        st.success("File loaded successfully")

        valid_columns = get_valid_columns(df)

        # Duration (safe)
        login_col, logout_col = detect_login_logout_columns(df)
        if login_col and logout_col:
            df = add_duration_column(df, login_col, logout_col)
            st.info(f"Duration calculated using '{login_col}' and '{logout_col}'")

        st.write("### Generating Data Quality Report...")

        # ==============================
        # REPORT
        # ==============================
        for col in valid_columns:
            if col == "Duration":
                continue

            st.markdown("---")
            st.subheader(f"📌 Column: {col}")

            # Missing = truly empty only
            missing_mask = df[col].isna() | df[col].astype(str).str.strip().eq("")
            missing_count = missing_mask.sum()

            if missing_count > 0:
                st.write(f"**Missing values:** {missing_count}")

                missing_df = df[missing_mask]
                display_cols = [c for c in valid_columns if c != col]

                st.write("Affected records (all other fields):")
                st.dataframe(missing_df[display_cols])
            else:
                st.write("✅ No missing values found.")

            # Date gap analysis (only if meaningful)
            if is_date_column(df[col]):
                gaps = find_date_gaps(df[col])
                if gaps:
                    st.write("**Date gaps detected:**")
                    for g in gaps:
                        st.write("•", g)
                else:
                    st.write("✅ No date gaps detected.")
            else:
                st.write("ℹ Date gap analysis not applicable.")

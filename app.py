import streamlit as st
import pandas as pd

from data_quality import (
    get_valid_columns,
    is_date_column,
    find_date_gaps,
    detect_login_logout_columns,
    add_duration_column
)

from anomaly_engine import detect_anomalies


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
# STREAMLIT UI
# ==============================
st.set_page_config(
    page_title="Hospital Data Quality Report",
    layout="wide"
)

st.title("🏥 Hospital Data Quality Assessment Report")

uploaded_file = st.file_uploader(
    "Upload Hospital Data (CSV / Excel)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    df = load_data(uploaded_file)

    if df is None:
        st.stop()

    st.success("File loaded successfully")

    st.subheader("📋 Actual Columns in Dataset")
    st.write(list(df.columns))

    # ==============================
    # DATA QUALITY ANALYSIS
    # ==============================
    valid_columns = get_valid_columns(df)

    login_col, logout_col = detect_login_logout_columns(df)
    if login_col and logout_col:
        df = add_duration_column(df, login_col, logout_col)
        st.info(f"Duration calculated using '{login_col}' and '{logout_col}'")

    st.markdown("---")
    st.header("📊 Data Quality Report")

    for col in valid_columns:
        if col == "Duration":
            continue

        st.markdown("---")
        st.subheader(f"📌 Column: {col}")

        missing_mask = df[col].isna() | df[col].astype(str).str.strip().eq("")
        missing_count = missing_mask.sum()

        if missing_count > 0:
            st.write(f"**Missing values:** {missing_count}")
            missing_df = df[missing_mask]
            display_cols = [c for c in valid_columns if c != col]
            st.dataframe(missing_df[display_cols])
        else:
            st.write("✅ No missing values found.")

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


    # ==============================
    # ANOMALY DETECTION (ML BASED)
    # ==============================
    st.markdown("---")
    st.header("🚨 ML-Based Anomaly Detection (Isolation Forest)")

    try:
        anomaly_df = detect_anomalies(df)

        if not anomaly_df.empty:
            st.metric("Total Anomalies Detected", len(anomaly_df))
            st.dataframe(anomaly_df)
        else:
            st.success("🎉 No anomalies detected.")

    except Exception as e:
        st.warning(f"There are no anomalies.")


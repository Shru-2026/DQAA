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
# SANITIZE USER INPUT
# ==============================
def sanitize_input(text):
    if not text:
        return None
    return text.strip().strip('"').strip("'").strip()

# ==============================
# COLUMN RESOLUTION
# ==============================
def resolve_column_name(user_input, df_columns):
    user_input = sanitize_input(user_input)
    if not user_input:
        return None
    user_input = user_input.lower()
    col_map = {col.lower(): col for col in df_columns}
    return col_map.get(user_input)

# ==============================
# CHECK DATE COLUMN
# ==============================
def is_date_column(series):
    try:
        pd.to_datetime(series.dropna().iloc[:10])
        return True
    except:
        return False

# ==============================
# FIND DATE GAPS
# ==============================
def find_date_gaps(df, date_col):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    dates = df[date_col].dropna().sort_values().unique()

    gaps = []
    for i in range(len(dates) - 1):
        if (dates[i+1] - dates[i]).days > 1:
            gaps.append(
                f"No records found between "
                f"{(dates[i] + timedelta(days=1)).strftime('%d %b %Y')} and "
                f"{(dates[i+1] - timedelta(days=1)).strftime('%d %b %Y')}"
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
# ADD DURATION COLUMN
# ==============================
def add_duration_column(df, login_col, logout_col):
    df = df.copy()
    df[login_col] = pd.to_datetime(df[login_col], errors="coerce")
    df[logout_col] = pd.to_datetime(df[logout_col], errors="coerce")
    df["Duration"] = (df[logout_col] - df[login_col]).apply(format_duration)
    return df

# ==============================
# GENERATE INSIGHTS
# ==============================
def generate_insights(df, target_col):
    insights = []

    if is_date_column(df[target_col]):
        insights.extend(find_date_gaps(df, target_col))

    missing_count = df[target_col].isna().sum()

    if missing_count > 0:
        insights.append(
            f"{missing_count} records are missing values in '{target_col}'."
        )
    else:
        insights.append(
            f"No missing values found in '{target_col}'."
        )

    return insights, missing_count

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="Hospital Data Quality Tool", layout="wide")

st.title("🏥 Hospital Data Quality & Assessment Tool")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    df = load_data(uploaded_file)

    if df is not None:
        st.success("File loaded successfully")

        st.write("### Available Columns (copy individually)")
        for col in df.columns:
            st.code(col)

        user_column = st.text_input(
            "Enter column name to analyze",
            placeholder="e.g. Visit Date"
        )

        display_columns = st.multiselect(
            "Select columns to display in output",
            options=list(df.columns)
        )

        if st.button("Analyze Data"):
            resolved_column = resolve_column_name(user_column, df.columns)

            if not resolved_column:
                st.error("Target column not found.")
            else:
                st.write(f"## Analysis for column: {resolved_column}")

                insights, missing_count = generate_insights(df, resolved_column)
                for insight in insights:
                    st.write("•", insight)

                # 🔑 ONLY proceed if missing data exists
                if missing_count > 0:
                    missing_df = df[df[resolved_column].isna()]

                    selected_lower = [c.lower() for c in display_columns]

                    # Duration only when missing rows exist
                    if "login time" in selected_lower and "logout time" in selected_lower:
                        df = add_duration_column(
                            df,
                            resolve_column_name("login time", df.columns),
                            resolve_column_name("logout time", df.columns),
                        )
                        st.info("Duration calculated from Login Time and Logout Time")

                    st.write("### Records with Missing Values")

                    cols_to_show = display_columns.copy()
                    if "Duration" in df.columns:
                        cols_to_show.append("Duration")

                    st.dataframe(missing_df[cols_to_show])

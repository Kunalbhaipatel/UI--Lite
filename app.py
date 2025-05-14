
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Shaker Dashboard", layout="wide")
st.title("🛠️ Shaker Health & Performance Dashboard")

# Sidebar Upload
st.sidebar.header("📤 Upload CSV")
uploaded_file = st.sidebar.file_uploader("Choose sensor file", type=["csv"])

if uploaded_file:
    max_rows = st.sidebar.slider("Rows to load", 5000, 200000, 50000, step=5000)
    usecols = [
        'YYYY/MM/DD', 'HH:MM:SS',
        'SHAKER #1 (Units)', 'SHAKER #2 (Units)', 'SHAKER #3 (PERCENT)',
        'Total Pump Output (gal_per_min)', 'DAS Vibe Lateral Max (g_force)'
    ]
    with st.spinner("Reading file..."):
        df = pd.read_csv(uploaded_file, usecols=usecols, nrows=max_rows)
        df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'])
        df.drop(columns=['YYYY/MM/DD', 'HH:MM:SS'], inplace=True)
        df.set_index('Timestamp', inplace=True)

    # Precompute metrics
    df['Shaker Capacity (GPM)'] = df['Total Pump Output (gal_per_min)'] / 3
    df['Performance Index'] = (100 - df['DAS Vibe Lateral Max (g_force)'] * 3).clip(0, 100)
    df['Overload Alert'] = (df['Shaker Capacity (GPM)'] > df['Performance Index']).astype(int)

    # KPI summary row
    col1, col2, col3 = st.columns(3)
    col1.metric("Max GPM", f"{df['Shaker Capacity (GPM)'].max():.1f}")
    col2.metric("Avg Performance", f"{df['Performance Index'].mean():.1f}%")
    col3.metric("Total Alerts", f"{df['Overload Alert'].sum()} ⚠️")

    # Tabbed layout
    tabs = st.tabs(["📈 Overview", "🔍 Diagnostics", "📊 Shaker Charts", "📄 Reports"])

    with tabs[0]:
        st.markdown("### Overview: Combined GPM and Performance")
        fig = px.line(df.reset_index(), x='Timestamp', y=['Shaker Capacity (GPM)', 'Performance Index'])
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.markdown("### Diagnostics Table (last 10 alerts)")
        st.dataframe(df[df['Overload Alert'] == 1].tail(10), use_container_width=True)

    with tabs[2]:
        shaker = st.selectbox("Choose Shaker", ["SHAKER #1 (Units)", "SHAKER #2 (Units)", "SHAKER #3 (PERCENT)"])
        fig = px.line(df.reset_index(), x='Timestamp', y=shaker, title=f"{shaker} Over Time")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.markdown("### 📄 Downloadable Alert Summary")

        if st.button("Generate PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Shaker Alert Summary", ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Rows loaded: {len(df)}", ln=True)
            pdf.cell(0, 10, f"Alerts triggered: {df['Overload Alert'].sum()}", ln=True)
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Recent Overload Events", ln=True)
            pdf.set_font("Arial", '', 10)
            alerts = df[df['Overload Alert'] == 1].tail(10)
            for idx, row in alerts.iterrows():
                line = f"{idx:%Y-%m-%d %H:%M:%S} | GPM: {row['Shaker Capacity (GPM)']:.1f} > Perf: {row['Performance Index']:.1f}"
                pdf.cell(0, 8, line, ln=True)
            pdf_file = "/mnt/data/best_shaker_alert_report.pdf"
            pdf.output(pdf_file)
            st.success("✅ PDF Report Generated")
            with open(pdf_file, "rb") as f:
                st.download_button("Download Report", f, file_name="shaker_alert_summary.pdf")

    # Sidebar CSV
    st.sidebar.download_button("Download Processed CSV", df.to_csv().encode(), "processed_shaker_data.csv")

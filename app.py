
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import timedelta

st.set_page_config(page_title="Shaker Alert PDF Export", layout="wide")
st.title("🛠️ Shaker Alert Dashboard with PDF Recommendations")

uploaded_file = st.sidebar.file_uploader("Upload your sensor CSV", type=["csv"])
if uploaded_file:
    usecols = [
        'YYYY/MM/DD', 'HH:MM:SS',
        'SHAKER #1 (Units)', 'SHAKER #2 (Units)', 'SHAKER #3 (PERCENT)',
        'Total Pump Output (gal_per_min)', 'DAS Vibe Lateral Max (g_force)'
    ]
    df = pd.read_csv(uploaded_file, usecols=usecols)
    df['Timestamp'] = pd.to_datetime(df['YYYY/MM/DD'] + ' ' + df['HH:MM:SS'])
    df.drop(columns=['YYYY/MM/DD', 'HH:MM:SS'], inplace=True)
    df.set_index('Timestamp', inplace=True)

    df['Shaker Capacity (GPM)'] = df['Total Pump Output (gal_per_min)'] / 3
    df['Performance Index'] = (100 - df['DAS Vibe Lateral Max (g_force)'] * 3).clip(0, 100)
    df['Overload Alert'] = (df['Shaker Capacity (GPM)'] > df['Performance Index']).astype(int)

    st.metric("Total Alerts", df['Overload Alert'].sum())
    st.dataframe(df[df['Overload Alert'] == 1].tail(10))

    def generate_pdf(df):
        pdf = FPDF()
pdf.image('Prodigy_IQ_logo.png', x=10, y=8, w=50)
pdf.ln(20)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Shaker Alert Summary Report", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Total rows: {len(df)}", ln=True)
        pdf.cell(0, 10, f"Alerts triggered: {df['Overload Alert'].sum()}", ln=True)
        pdf.ln(6)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Alert Details", ln=True)
        pdf.set_font("Arial", '', 10)
        recommendations = {
            'overload': "Reduce pump rate or inspect screen load.",
            'high_vibe': "Check for mechanical imbalance or worn screen.",
            'general': "Monitor shaker speed and clean screens."
        }
        alerts = df[df['Overload Alert'] == 1].tail(10)
        for idx, row in alerts.iterrows():
            line = f"{idx:%Y-%m-%d %H:%M:%S} | GPM: {row['Shaker Capacity (GPM)']:.1f} > Perf: {row['Performance Index']:.1f}"
            pdf.cell(0, 8, line, ln=True)
            pdf.set_font("Arial", 'I', 9)
            pdf.multi_cell(0, 8, f"→ Recommendation: {recommendations['overload']}")
            pdf.set_font("Arial", '', 10)
        output_path = "/mnt/data/shaker_alert_recommendations.pdf"
        pdf.output(output_path)
        return output_path

    if st.button("📄 Generate PDF Summary"):
        report_path = generate_pdf(df)
        with open(report_path, "rb") as f:
            st.download_button("Download PDF Report", f, file_name="shaker_alert_summary.pdf")

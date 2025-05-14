import streamlit as st
from datetime import date

st.set_page_config(page_title="AgriPrice Predictor", layout="wide")

# --- Sidebar Menu ---
with st.sidebar:
    st.markdown("## Menu")
    st.markdown("🧭 **Dashboard**")
    st.markdown("📈 **PricePrediction**")
    st.markdown("🌾 **Crop Selection**")
    st.markdown("📊 **Historical Data**")
    st.markdown("⚙️ **Setting**")

# --- Header ---
st.markdown("<h1 style='color: white; background-color: #28C76F; padding: 10px; border-radius: 5px;'>AgriPrice predictor</h1>", unsafe_allow_html=True)

# --- Price Prediction Section ---
st.markdown("### Price Prediction")

col1, col2 = st.columns([2, 1])
with col1:
    crop = st.selectbox("Select crop", ["Maize", "Rice", "Wheat"])
with col2:
    selected_date = st.date_input("Select date", value=date.today())

# --- Predicted Price Box ---
st.markdown("""
<div style='background-color: #EAF6FF; padding: 15px; border-radius: 10px; margin-top: 20px;'>
    <h3>🪙 <strong style="color:#000">2,250 per Kilogram</strong></h3>
    <p style='color: #666;'>Maize, Next Month Prediction</p>
</div>
""", unsafe_allow_html=True)

# --- Prediction Confidence ---
st.markdown("""
<div style='background-color: #E3FCEC; padding: 10px; border-radius: 10px; border: 1px solid #28C76F; margin-top: 10px;'>
    <strong style='color: #28C76F;'>Prediction Confidence: 85%</strong>
</div>
""", unsafe_allow_html=True)

# --- Factors Influencing Price ---
st.markdown("#### Factor influencing Price")
factors = {
    "🌧️ Rainfall": True,
    "🌡️ Temperature": True,
    "🚜 Agriculture inputs": True,
    "📈 Market Demand": True,
    "🌐 Globla Trade": True,
    "✅ Economic Indicators": True
}
st.markdown("<div style='background-color: #F9F9F9; padding: 15px; border-radius: 10px;'>", unsafe_allow_html=True)
cols = st.columns(3)
for i, (label, enabled) in enumerate(factors.items()):
    with cols[i % 3]:
        st.markdown(f"<p style='font-size: 16px;'>{label}</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

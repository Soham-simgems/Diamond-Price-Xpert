import streamlit as st
import pandas as pd
import os
from PIL import Image

# ------------------------------
# UI Configuration
# ------------------------------
st.set_page_config(page_title="SIM GEMS DiamondPriceXpert", layout="centered")
st.markdown("""
<div style='text-align: center;'>
    <h2>💎 Diamond Price Xpert</h2>
    <h4>Your Ultimate Diamond Pricing Assistant</h4>
</div>
""", unsafe_allow_html=True)

# ------------------------------
# Load Rapaport Data
# ------------------------------
@st.cache_data
def load_data():
    df_round = pd.read_csv("CSV2_ROUND_8_4.csv", header=None)
    df_fancy = pd.read_csv("CSV2_PEAR_8_4.csv", header=None)

    df_round.columns = ["Shape", "Clarity", "Color", "From_Wt", "To_Wt", "Rap_Price_Ct", "Date"]
    df_fancy.columns = ["Shape", "Clarity", "Color", "From_Wt", "To_Wt", "Rap_Price_Ct", "Date"]

    df_round["Date"] = pd.to_datetime(df_round["Date"], errors="coerce")
    df_fancy["Date"] = pd.to_datetime(df_fancy["Date"], errors="coerce")

    return df_round, df_fancy

df_round, df_fancy = load_data()

# ------------------------------
# Mappings
# ------------------------------
shape_display = [
    "Round", "Pear", "Emerald", "Radiant", "Oval",
    "Cush Brill", "Princess", "Heart", "Marquise", "Asscher", "Kite"
]
shape_mapping = {shape: ("BR" if shape == "Round" else "PS") for shape in shape_display}
color_options = list("DEFGHIJKLM")
clarity_options = ["FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "SI3", "I1", "I2", "I3"]

# ------------------------------
# 1. Weight Input
# ------------------------------
st.markdown("### ⚖️ Enter Diamond Weight (in carats)")
weight = st.number_input("Enter weight", min_value=0.0, step=0.01, format="%.2f")

# ------------------------------
# 2. Shape Selection
# ------------------------------
st.markdown("### 💠 Select Shape")
image_dir = "shapes/"
cols_per_row = 4
selected_shape = st.session_state.get("selected_shape", None)

for i in range(0, len(shape_display), cols_per_row):
    cols = st.columns(cols_per_row)
    for col, shape in zip(cols, shape_display[i:i + cols_per_row]):
        image_file = f"{shape.lower().replace(' ', '_')}.png"
        image_path = os.path.join(image_dir, image_file)

        with col:
            if os.path.exists(image_path):
                img = Image.open(image_path).resize((60, 60))
                if col.button(f"⬇️ {shape}", key=f"btn_{shape}"):
                    st.session_state["selected_shape"] = shape
                col.image(img, use_container_width=False)
            else:
                st.warning(f"{shape} image missing")

if st.session_state.get("selected_shape"):
    st.success(f"✅ Selected Shape: {st.session_state['selected_shape']}")
    shape_code = shape_mapping.get(st.session_state["selected_shape"], None)
# ------------------------------
# Color Selection
# ------------------------------
st.markdown("### 🎨 Select Color")

cols_color_1 = st.columns(6)
cols_color_2 = st.columns(6)

# First 6 colors: D–I
for col, color in zip(cols_color_1, color_options[:6]):
    with col:
        if st.button(color, key=f"color_{color}"):
            st.session_state["selected_color"] = color

# Remaining 5 colors: J–M
for col, color in zip(cols_color_2, color_options[6:]):
    with col:
        if st.button(color, key=f"color_{color}"):
            st.session_state["selected_color"] = color

if st.session_state.get("selected_color"):
    st.success(f"✅ Selected Color: {st.session_state['selected_color']}")
# ------------------------------
# Clarity Selection
# ------------------------------
st.markdown("### 🔎 Select Clarity")

cols_clarity_1 = st.columns(7)
cols_clarity_2 = st.columns(6)

# First 7 clarities
for col, clarity in zip(cols_clarity_1, clarity_options[:7]):
    with col:
        if st.button(clarity, key=f"clarity_{clarity}"):
            st.session_state["selected_clarity"] = clarity

# Remaining 6 clarities
for col, clarity in zip(cols_clarity_2, clarity_options[7:]):
    with col:
        if st.button(clarity, key=f"clarity_{clarity}"):
            st.session_state["selected_clarity"] = clarity

if st.session_state.get("selected_clarity"):
    st.success(f"✅ Selected Clarity: {st.session_state['selected_clarity']}")

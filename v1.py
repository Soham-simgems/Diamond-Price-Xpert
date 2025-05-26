import streamlit as st
import pandas as pd
#from forex_python.converter import CurrencyRates
import requests


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
    df_round = pd.read_csv("CSV2_ROUND_8_4 (4).csv", header=None)
    df_fancy = pd.read_csv("CSV2_PEAR_8_4 (3).csv", header=None)

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
    "Round", "Princess", "Emerald", "Asscher", "Marquise",
    "Oval", "Radiant", "Pear", "Heart", "Cushion"
]
shape_mapping = {shape: ("BR" if shape == "Round" else "PS") for shape in shape_display}
color_options = list("DEFGHIJKLM")
clarity_options = ["FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "SI3", "I1", "I2", "I3"]

# ------------------------------
# Form UI
# ------------------------------
st.markdown("### 📥 Enter Diamond Details")
col1, col2 = st.columns(2)
with col1:
    weight = st.number_input("Stone Weight (Cts)", min_value=0.01, value=0.30, step=0.01, format="%.2f")
    shape_ui = st.selectbox("Shape", shape_display)
with col2:
    color = st.selectbox("Color", color_options)
    clarity = st.selectbox("Clarity", clarity_options)

# Shape mapping and weight logic
shape_code = shape_mapping[shape_ui]
clarity_lookup = "IF" if clarity == "FL" else clarity

use_5cts_price = st.checkbox("Use 5 Cts Rap Price")

# ------------------------------
# Discount Selection
# ------------------------------
st.markdown("### 💲 Discount Selection")
disc_col1, disc_col2, disc_val_col = st.columns([1, 1, 2])

if "discount_mode" not in st.session_state:
    st.session_state.discount_mode = "-"

# Buttons with shadow logic
button_style = """
<style>
button[data-baseweb="button"] {
    transition: box-shadow 0.3s ease;
}
button[data-baseweb="button"]:active {
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
}
</style>
"""
st.markdown(button_style, unsafe_allow_html=True)

with disc_col1:
    if st.button("➕"):
        st.session_state.discount_mode = "-"
with disc_col2:
    if st.button("➖"):
        st.session_state.discount_mode = "+"

with disc_val_col:
    disc_val = st.number_input("Enter Discount Value", value=10)

# Mode logic fix: now + means negative discount (price goes up), - means positive discount
if st.session_state.discount_mode == "+":
    discount = abs(disc_val)
else:
    discount = -abs(disc_val)
# ------------------------------
# Last Updated Rapaport Date Display
# ------------------------------
latest_date_round = df_round["Date"].dropna().max()
latest_date_fancy = df_fancy["Date"].dropna().max()
latest_date = max(latest_date_round, latest_date_fancy)

if pd.notna(latest_date):
    last_updated_str = latest_date.strftime("%d %B %Y")
    st.markdown(f"""
    <div style='text-align: center; margin-top: -10px; margin-bottom: 30px;'>
        <span style="font-size:16px;">✅Last Updated Rapaport data - <b>{last_updated_str}</b></span>
    </div>
    """, unsafe_allow_html=True)
# ------------------------------
# Rapaport Matching Logic
# ------------------------------
# Fixed logic for matching rapaport price based on weight
# Apply search logic based on weight
if use_5cts_price and weight >= 5.00:
    search_weight = 5.00
elif weight >= 10.00:
    search_weight = 10.00
elif 6.00 <= weight < 10.00:
    search_weight = 5.00
else:
    search_weight = weight

df = df_round if shape_code == "BR" else df_fancy

match = df[
    (df["Shape"] == shape_code) &
    (df["Clarity"] == clarity_lookup) &
    (df["Color"] == color) &
    (df["From_Wt"] <= search_weight) &
    (df["To_Wt"] >= search_weight)
]

if not match.empty:
    rap_price_ct = match.iloc[0]["Rap_Price_Ct"]
    #st.success(f"✅ Rapaport Price/Ct: ${rap_price_ct:.2f}")
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; background-color: #d4edda; 
                color: #155724; border-radius: 5px; border: 1px solid #c3e6cb;">
        ✅ <strong>Rapaport Price/Ct:</strong> ${rap_price_ct:.2f}
    </div>
    """, unsafe_allow_html=True)
    # Calculations
    price_per_ct = rap_price_ct * (1 - discount / 100)
    total_usd = price_per_ct * weight

   #@st.cache_data(ttl=3600)
       # @st.cache_data(ttl=3600)
    @st.cache_data(ttl=3600)
    def get_usd_to_inr_rate():
        try:
            #API_KEY = "f11bd00cea39e977eb162a6e7f47b4b3"  # Replace with your actual API key
            url = f"http://api.exchangerate.host/live?access_key={API_KEY}&source=USD&currencies=INR&format=1"
            response = requests.get(url, timeout=5)
            data = response.json()

            if data.get("success") and "quotes" in data and "USDINR" in data["quotes"]:
                return data["quotes"]["USDINR"]
            else:
                st.warning(f"⚠️ Unexpected response format. Using fallback rate ₹85.50.\n\nFull response: {data}")
                return 85.50
        except Exception as e:
            st.warning(f"⚠️ Could not fetch live INR rate. Using fallback rate ₹85.50.\n\nError: {e}")
            return 85.50

    inr_rate = get_usd_to_inr_rate()  # 💸 get latest conversion rate
    total_inr = total_usd * inr_rate

    # Editable Fields
    colx, coly = st.columns(2)
    with colx:
        price_per_ct_input = st.number_input("Price per Ct (USD)", value=round(price_per_ct, 2))
    with coly:
        total_usd_input = st.number_input("Total Price (USD)", value=round(total_usd, 2))

    if price_per_ct_input != round(price_per_ct, 2):
        discount = (1 - (price_per_ct_input / rap_price_ct)) * 100
        total_usd_input = price_per_ct_input * weight
    elif total_usd_input != round(total_usd, 2):
        price_per_ct_input = total_usd_input / weight
        discount = (1 - (price_per_ct_input / rap_price_ct)) * 100

    total_inr = total_usd_input * inr_rate

    # ------------------------------
    # Final Summary Display
    # ------------------------------
    st.markdown(f"""
    <div style="text-align:center; padding:15px; background-color:#f0f8ff; border-radius:10px; font-size:16px;">
    <b>💸 Discount:</b> {-discount:.2f}%<br>
    <b>💰 Price per Ct (USD):</b> ${price_per_ct_input:.2f}<br>
    <b>💵 Total Price (USD):</b> ${total_usd_input:.2f}<br>
    <b>🌍 USD to INR Rate:</b> ₹{inr_rate:.2f}<br>
    <b>💷 Total Price (INR):</b> ₹{total_inr:,.2f}
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("❌ No matching Rapaport price found for this combination.")

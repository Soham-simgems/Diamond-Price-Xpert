import streamlit as st
import pandas as pd
import requests


# ------------------------------
# UI Configuration
# ------------------------------
st.set_page_config(page_title="DiamondPriceXpert", layout="centered")
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
    "Round", "Princess", "Emerald", "Asscher", "Marquise",
    "Oval", "Radiant", "Pear", "Heart", "Cushion"
]
# Your original mapping only has BR and PS - likely you want BR for Round and PS for all others
shape_mapping = {shape: ("BR" if shape == "Round" else "PS") for shape in shape_display}

color_options = list("DEFGHIJKLM")
clarity_options = ["FL", "IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "SI3", "I1", "I2", "I3"]


# ------------------------------
# Function to get Rapaport Price based on criteria
# ------------------------------
def get_rap_price(df, shape_code, clarity, color, weight, use_5cts_price):
    clarity_lookup = "IF" if clarity == "FL" else clarity

    # Weight logic
    if use_5cts_price and weight >= 5.0:
        search_weight = 5.0
    elif weight >= 10.0:
        search_weight = 10.0
    elif 6.0 <= weight < 10.0:
        search_weight = 5.0
    else:
        search_weight = weight

    match = df[
        (df["Shape"] == shape_code) &
        (df["Clarity"] == clarity_lookup) &
        (df["Color"] == color) &
        (df["From_Wt"] <= search_weight) &
        (df["To_Wt"] >= search_weight)
    ]

    if not match.empty:
        return match.iloc[0]["Rap_Price_Ct"]
    else:
        return None


# ------------------------------
# Currency Conversion
# ------------------------------
@st.cache_data(ttl=3600)
def get_usd_to_inr_rate():
        try:
            API_KEY = "f11bd00cea39e977eb162a6e7f47b4b3"  # Replace with your actual API key
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


# ------------------------------
# Main UI: Mode selection
# ------------------------------
mode = st.radio("Choose Mode", ["Single Stone Calculator", "Recut Calculator"])


if mode == "Single Stone Calculator":
    # ------------------------------
    # Form UI
    # ------------------------------
    st.markdown("### 📥 Enter Diamond Details")
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("Weight (Cts)", min_value=0.01, value=0.30, step=0.01, format="%.2f")
        shape_ui = st.selectbox("Shape", shape_display)
    with col2:
        color = st.selectbox("Color", color_options)
        clarity = st.selectbox("Clarity", clarity_options)

    shape_code = shape_mapping[shape_ui]

    use_5cts_price = st.checkbox("Use 5 Cts Rap Price")

    # Discount Section
    st.markdown("### 💲 Discount Selection")
    disc_col1, disc_col2, disc_val_col = st.columns([1, 1, 2])

    if "discount_mode" not in st.session_state:
        st.session_state.discount_mode = "-"

    with disc_col1:
        if st.button("➕"):
            st.session_state.discount_mode = "-"
    with disc_col2:
        if st.button("➖"):
            st.session_state.discount_mode = "+"

    with disc_val_col:
        disc_val = st.number_input("Enter Discount Value (%)", value=10.0, min_value=0.0, max_value=100.0)

    if st.session_state.discount_mode == "+":
        discount = abs(disc_val)
    else:
        discount = -abs(disc_val)

    # Rapaport Data Matching and Price Calculation
    df = df_round if shape_code == "BR" else df_fancy

    rap_price_ct = get_rap_price(df, shape_code, clarity, color, weight, use_5cts_price)

    if rap_price_ct is not None:
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: #d4edda; 
                    color: #155724; border-radius: 5px; border: 1px solid #c3e6cb;">
            ✅ <strong>Rapaport Price/Ct:</strong> ${rap_price_ct:.2f}
        </div>
        """, unsafe_allow_html=True)


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
                <span style="font-size:16px;"><br>✅Last Updated Rapaport data - <b>{last_updated_str}</b></span>
            </div>
            """, unsafe_allow_html=True)
        # ------------------------------

        price_per_ct = rap_price_ct * (1 - discount / 100)
        total_usd = price_per_ct * weight

        inr_rate = get_usd_to_inr_rate()
        total_inr = total_usd * inr_rate

        colx, coly = st.columns(2)
        with colx:
            price_per_ct_input = st.number_input("Price per Ct (USD)", value=round(price_per_ct, 2))
        with coly:
            total_usd_input = st.number_input("Total Price (USD)", value=round(total_usd, 2))

        # Adjust discount if user edits price fields
        if price_per_ct_input != round(price_per_ct, 2):
            discount = (1 - (price_per_ct_input / rap_price_ct)) * 100
            total_usd_input = price_per_ct_input * weight
        elif total_usd_input != round(total_usd, 2):
            price_per_ct_input = total_usd_input / weight
            discount = (1 - (price_per_ct_input / rap_price_ct)) * 100

        total_inr = total_usd_input * inr_rate

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

else:
    # ------------------------------
    # Recut Pricing Calculator (Two Stones)
    # ------------------------------
    st.markdown("### 📥 Enter Diamond Details")


        # ------------------------------
    # Input Section for Both Diamonds
    # ------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📍 Diamond A")
        weight1 = st.number_input("Weight (Cts)", min_value=0.01, value=0.30, step=0.01, key="w1")
        shape1 = st.selectbox("Shape", shape_display, key="s1")
        color1 = st.selectbox("Color", color_options, key="c1")
        clarity1 = st.selectbox("Clarity", clarity_options, key="cl1")

    with col2:
        st.markdown("#### 📍 Diamond B")
        weight2 = st.number_input("Weight (Cts)", min_value=0.01, value=0.30, step=0.01, key="w2")
        shape2 = st.selectbox("Shape", shape_display, key="s2")
        color2 = st.selectbox("Color", color_options, key="c2")
        clarity2 = st.selectbox("Clarity", clarity_options, key="cl2")

    # ------------------------------
    # Discount Selection for Both Diamonds
    # ------------------------------
    st.markdown("### 💲 Discount Selection")

    if "discount_mode_A" not in st.session_state:
        st.session_state.discount_mode_A = "-"
    if "discount_mode_B" not in st.session_state:
        st.session_state.discount_mode_B = "-"

    # Diamond A Discount Inputs
    with st.expander("🔻 Diamond A Discount"):
        d1col1, d1col2, d1val = st.columns([1, 1, 2])
        with d1col1:
            if st.button("➕ A", key="plus_a"):
                st.session_state.discount_mode_A = "-"
        with d1col2:
            if st.button("➖ A", key="minus_a"):
                st.session_state.discount_mode_A = "+"
        with d1val:
            disc_val_a = st.number_input("Discount A (%)", min_value=0.0, max_value=100.0, value=10.0, key="dval_a")

    # Diamond B Discount Inputs
    with st.expander("🔻 Diamond B Discount"):
        d2col1, d2col2, d2val = st.columns([1, 1, 2])
        with d2col1:
            if st.button("➕ B", key="plus_b"):
                st.session_state.discount_mode_B = "-"
        with d2col2:
            if st.button("➖ B", key="minus_b"):
                st.session_state.discount_mode_B = "+"
        with d2val:
            disc_val_b = st.number_input("Discount B (%)", min_value=0.0, max_value=100.0, value=10.0, key="dval_b")

    # Process discount values
    discount_a = -abs(disc_val_a) if st.session_state.discount_mode_A == "-" else abs(disc_val_a)
    discount_b = -abs(disc_val_b) if st.session_state.discount_mode_B == "-" else abs(disc_val_b)

    # ------------------------------
    # Function to Calculate and Display Pricing
    # ------------------------------
    use_5cts_price = st.checkbox("Use 5 Cts Rap Price", value=False)

    def calculate_diamond_price(shape, weight, color, clarity, label, discount, use_5cts_price):
        shape_code = "BR" if shape == "Round" else "PS"
        df = df_round if shape_code == "BR" else df_fancy
        rap_price_ct = get_rap_price(df, shape_code, clarity, color, weight, use_5cts_price)

        if rap_price_ct is None:
            st.error(f"❌ No Rapaport price found for {label}.")
            return None, None, None, None

        price_per_ct = rap_price_ct * (1 - discount / 100)
        total_usd = price_per_ct * weight

        inr_rate = get_usd_to_inr_rate()
        total_inr = total_usd * inr_rate

        colx, coly = st.columns(2)
        with colx:
            price_per_ct_input = st.number_input(f"{label} - Price per Ct (USD)", value=round(price_per_ct, 2))
        with coly:
            total_usd_input = st.number_input(f"{label} - Total Price (USD)", value=round(total_usd, 2))

        # Adjust discount if user edits price fields
        if price_per_ct_input != round(price_per_ct, 2):
            discount = (1 - (price_per_ct_input / rap_price_ct)) * 100
            total_usd_input = price_per_ct_input * weight
        elif total_usd_input != round(total_usd, 2):
            price_per_ct_input = total_usd_input / weight if weight != 0 else 0
            discount = (1 - (price_per_ct_input / rap_price_ct)) * 100

        total_inr = total_usd_input * inr_rate

        st.markdown(f"### 💎 {label} Price Summary")
        st.markdown(f"""
        <div style="text-align:center; padding:15px; background-color:#f0f8ff; border-radius:10px; font-size:16px;">
        <b>✅ Rapaport Price/Ct:</b> ${rap_price_ct:.2f}<br>
        <b>💸 Discount:</b> {-discount:.2f}%<br>
        <b>💰 Price per Ct (USD):</b> ${price_per_ct_input:.2f}<br>
        <b>💵 Total Price (USD):</b> ${total_usd_input:.2f}<br>
        <b>🌍 USD to INR Rate:</b> ₹{inr_rate:.2f}<br>
        <b>💷 Total Price (INR):</b> ₹{total_inr:,.2f}
        </div>
        """, unsafe_allow_html=True)

        # Return updated discount and key price values for further summary
        return total_usd_input, weight, rap_price_ct, discount


    # ------------------------------
    # Run Price Calculations
    # ------------------------------
    st.markdown("---")

    total_usd_1, weight1, rap_price1, discount_a = calculate_diamond_price(
    shape1, weight1, color1, clarity1, "Diamond A", discount_a, use_5cts_price)
    total_usd_2, weight2, rap_price2, discount_b = calculate_diamond_price(
    shape2, weight2, color2, clarity2, "Diamond B", discount_b, use_5cts_price)
   # ------------------------------
    # Show Latest Rapaport Update
    # ------------------------------
    latest_date_round = df_round["Date"].dropna().max()
    latest_date_fancy = df_fancy["Date"].dropna().max()
    latest_date = max(latest_date_round, latest_date_fancy)

    if pd.notna(latest_date):
        last_updated_str = latest_date.strftime("%d %B %Y")
        st.markdown(f"""
        <div style='text-align: center; margin-top: 20px;'>
            ✅ <span style="font-size:16px;">Last Updated Rapaport data: <b>{last_updated_str}</b></span>
        </div>
        """, unsafe_allow_html=True)

    diff_usd = total_usd_2 - total_usd_1

    cost_usd = 0
    if weight2 != 0 and rap_price2 != 0:
        cost_usd = ((total_usd_1 / weight2) / rap_price2 - 1) * 100

    up_down_percent = 0
    if total_usd_1 != 0:
        up_down_percent = ((total_usd_2 - total_usd_1) / total_usd_1) * 100

    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center;'>
            <h3>📊 Final Cost Summary</h3>
            <p><strong>Difference in Total Price (USD):</strong> ${diff_usd:.2f}</p>
            <p><strong>Cost %:</strong> {cost_usd:.2f}%</p>
            <p><strong>Up/Down %:</strong> {up_down_percent:.2f}%</p>
        </div>
        """,
        unsafe_allow_html=True
    )
# ------------------------------
st.markdown(
    """
    <hr style="border: 0.5px solid #ccc;" />
    <div style='text-align: center; font-size: 16px; padding-top: 12px; color: #444;'>
        <strong> © 2025 Developed by Soham Jagtap| Data Analyst </strong> <br>
        🔗 <a href='https://github.com/Soham2543' target='_blank' style='text-decoration: none; color: #0366d6;'>GitHub</a> |
        💼 <a href='https://www.linkedin.com/in/sohamvjagtap/' target='_blank' style='text-decoration: none; color: #0a66c2;'>LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True
)
#st.markdown("---")
st.markdown(
    "<br><p style='text-align:center; font-size:16px;'>🚀 <strong>You're using Version 1.0</strong><br>"
    " Please share your valuable feedback at <a href='mailto:soham.jagtap@simgems.com'> <br>📧SohamJagtap</a></p>",
    unsafe_allow_html=True
)


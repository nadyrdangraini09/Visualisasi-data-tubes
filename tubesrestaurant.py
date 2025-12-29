import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

# =========================
# 1) Page configuration
# =========================
st.set_page_config(layout="wide", page_title="Houston Restaurant Explorer")

# =========================
# 2) CSS Injection (Fix sidebar input/select text color)
# =========================
st.markdown(
    """
<style>
.main { background-color: #1a1a2e !important; }

body, [data-testid="stAppViewContainer"] {
    background-color: #1a1a2e !important;
}

/* Force all text elements to WHITE */
[data-testid="stAppViewContainer"] * {
    color: #ffffff !important;
}

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] h5,
[data-testid="stAppViewContainer"] h6,
[data-testid="stAppViewContainer"] b,
[data-testid="stAppViewContainer"] strong,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] div {
    color: #ffffff !important;
}

/* Sidebar container */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg, #4f46e5, #4338ca);
    padding: 20px;
}

/* Sidebar text WHITE */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] * {
    color: white !important;
}

/* Input fields - BLACK text */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    color: #ffffff !important;
    background-color: #2a2a3e !important;
    caret-color: #ffffff !important;
}

[data-testid="stSidebar"] input::selection {
    background-color: #4f46e5 !important;
    color: #ffffff !important;
}

[data-testid="stSidebar"] input::placeholder {
    color: #6b7280 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #ffffff !important;
}

[data-testid="stSidebar"] [data-baseweb="popover"] * {
    color: #111827 !important;
}

[data-testid="stSidebar"] [data-testid="stSlider"] * {
    color: white !important;
}

/* Buttons */
.stButton > button {
    width: 100%;
    border-radius: 14px;
    padding: 12px;
    font-weight: 600;
    background: rgba(255,255,255,0.18);
    border: none;
    transition: 0.3s;
    color: white !important;
}

.stButton > button:hover {
    background: rgba(255,255,255,0.35);
    transform: translateY(-2px);
}

/* Card container - TRANSPARENT background with border */
.card {
    background: transparent !important;
    border-radius: 18px;
    padding: 22px;
    border: 1px solid rgba(255,255,255,0.15) !important;
    box-shadow: none !important;
    margin-bottom: 18px;
}

/* Force ALL text inside card to be WHITE */
.card,
.card * {
    color: #ffffff !important;
    fill: #ffffff !important;
}

.card p {
    color: #ffffff !important;
}

.card b,
.card strong,
.card span,
.card label,
.card div {
    color: #ffffff !important;
}

/* KPI */
.kpi {
    background: linear-gradient(135deg, #6366f1, #818cf8);
    color: white;
    border-radius: 18px;
    padding: 20px;
    text-align: center;
}

.kpi h2 { 
    margin: 0; 
    font-size: 30px;
    color: white !important;
}

.kpi p { 
    opacity: 0.9;
    color: white !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# 3) Load data
# =========================
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("restaurants.csv", on_bad_lines="skip")

    # --- Data transformation ---
    price_mapping = {"$": "Budget", "$$": "Mid-range", "$$$": "Expensive", "$$$$": "Luxury"}
    df["priceRange"] = df["priceRange"].map(price_mapping)

    bool_mapping = {True: "Yes", False: "No"}
    df["asapPickupAvailable"] = df["asapPickupAvailable"].map(bool_mapping)
    df["asapDeliveryAvailable"] = df["asapDeliveryAvailable"].map(bool_mapping)

    # Clean coordinates and numeric columns
    df = df.dropna(subset=["latitude", "longitude"])
    df["averageRating"] = pd.to_numeric(df["averageRating"], errors="coerce")
    df["asapDeliveryTimeMinutes"] = pd.to_numeric(df["asapDeliveryTimeMinutes"], errors="coerce")
    df["asapPickupMinutes"] = pd.to_numeric(df["asapPickupMinutes"], errors="coerce")

    return df


try:
    data = load_data()

    # =========================
    # HEADER
    # =========================
    st.title("Houston Restaurant Interactive Explorer")

    st.markdown(
        """
<div class="card" style="color: #ffffff !important;">
<p style="margin:0; line-height:1.6; color: #ffffff !important;">
    The primary objective of this dashboard is to provide an <b style="color: #ffffff !important;">interactive data visualization</b> that enables users
    to explore the spatial distribution and key characteristics of restaurants in Houston in an intuitive and efficient way.
    Using dynamic filters such as <b style="color: #ffffff !important;">price category</b>, <b style="color: #ffffff !important;">rating</b>, <b style="color: #ffffff !important;">delivery time</b>, <b style="color: #ffffff !important;">pickup time</b>, and
    <b style="color: #ffffff !important;">pickup/delivery availability</b>, users can quickly refine the results to restaurants that best match their preferences.
    This dashboard is designed to support a more <b style="color: #ffffff !important;">transparent</b>, <b style="color: #ffffff !important;">data-driven</b>, and <b style="color: #ffffff !important;">easy-to-understand</b> exploration experience.
</p>
<p style="margin:10px 0 0 0; opacity:0.85; color: #ffffff !important;">
    Dataset: Kaggle – Restaurants (GraphQuest)
</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # =========================
    # SIDEBAR FILTERS
    # =========================
    st.sidebar.header("Search Filters")
    search_query = st.sidebar.text_input("Search Restaurant Name", "")

    price_order = ["Budget", "Mid-range", "Expensive", "Luxury"]
    available_prices = [p for p in price_order if p in data["priceRange"].dropna().unique()]
    selected_price = st.sidebar.multiselect("Price Category", available_prices, default=available_prices)

    max_rating = st.sidebar.slider("Maximum Rating", 0.0, 5.0, 5.0, 0.1)

    max_del_time_val = data["asapDeliveryTimeMinutes"].max()
    max_del_time = int(max_del_time_val) if pd.notna(max_del_time_val) else 0
    selected_del_time = st.sidebar.slider("Maximum Delivery Time (Minutes)", 0, max_del_time, max_del_time)

    max_pick_time_val = data["asapPickupMinutes"].max()
    max_pick_time = int(max_pick_time_val) if pd.notna(max_pick_time_val) else 0
    selected_pick_time = st.sidebar.slider("Maximum Pickup Time (Minutes)", 0, max_pick_time, max_pick_time)

    selected_pickup = st.sidebar.selectbox("Pickup Available?", ["All", "Yes", "No"])
    selected_delivery = st.sidebar.selectbox("Delivery Available?", ["All", "Yes", "No"])

    map_measure = st.sidebar.selectbox(
        "Map Point Size Based On:",
        ["Restaurant Rating", "Delivery Time", "Pickup Time"],
    )

    # =========================
    # FILTERING LOGIC
    # =========================
    mask = (
        (data["averageRating"] <= max_rating)
        & (data["priceRange"].isin(selected_price))
        & (data["asapDeliveryTimeMinutes"] <= selected_del_time)
        & (data["asapPickupMinutes"] <= selected_pick_time)
    )

    if selected_pickup != "All":
        mask = mask & (data["asapPickupAvailable"] == selected_pickup)

    if selected_delivery != "All":
        mask = mask & (data["asapDeliveryAvailable"] == selected_delivery)

    if search_query.strip():
        mask = mask & (data["name"].astype(str).str.contains(search_query, case=False, na=False))

    filtered = data[mask]

    # =========================
    # SECTION 1: MAP
    # =========================
    st.subheader("📍 Restaurant Location Map")

    if map_measure == "Restaurant Rating":
        radius_calc = "averageRating * 15"
        point_color = "[255, 165, 0, 160]"  # orange
    elif map_measure == "Delivery Time":
        radius_calc = "asapDeliveryTimeMinutes * 2"
        point_color = "[0, 200, 100, 160]"  # green
    else:
        radius_calc = "asapPickupMinutes * 5"
        point_color = "[0, 100, 255, 160]"  # blue

    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            initial_view_state=pdk.ViewState(
                latitude=filtered["latitude"].mean() if not filtered.empty else 29.76,
                longitude=filtered["longitude"].mean() if not filtered.empty else -95.36,
                zoom=11,
                pitch=30,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=filtered,
                    get_position="[longitude, latitude]",
                    get_fill_color=point_color,
                    get_radius=radius_calc,
                    pickable=True,
                )
            ],
            tooltip={
                "html": (
                    "<b>{name}</b><br/>"
                    "Rating: {averageRating} ⭐<br/>"
                    "Price: {priceRange}<br/>"
                    "Delivery: {asapDeliveryAvailable}<br/>"
                    "Pickup: {asapPickupAvailable}"
                )
            },
        )
    )

    st.divider()

    # =========================
    # SECTION 2: FILTERED ANALYTICS
    # =========================
    st.subheader("📊 Filtered Data Analysis")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Restaurants Found", len(filtered))
    k2.metric("Average Rating", f"{filtered['averageRating'].mean():.2f}" if not filtered.empty else "0")
    k3.metric("Avg. Delivery Time", f"{int(filtered['asapDeliveryTimeMinutes'].mean())} min" if not filtered.empty else "0")
    k4.metric("Avg. Pickup Time", f"{int(filtered['asapPickupMinutes'].mean())} min" if not filtered.empty else "0")

    if not filtered.empty:
        st.markdown("---")

        st.write("**Pickup & Delivery Availability**")
        pickup_counts = filtered["asapPickupAvailable"].value_counts()
        delivery_counts = filtered["asapDeliveryAvailable"].value_counts()

        b1, b2 = st.columns(2)
        with b1:
            st.caption("Pickup")
            st.bar_chart(pickup_counts, use_container_width=True)
        with b2:
            st.caption("Delivery")
            st.bar_chart(delivery_counts, use_container_width=True)

        st.markdown("---")

        st.write("**Price Category Distribution**")
        price_counts = filtered["priceRange"].value_counts().reset_index()
        price_counts.columns = ["Category", "Count"]

        fig_price = px.pie(
            price_counts,
            values="Count",
            names="Category",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.4,
        )
        fig_price.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_price, use_container_width=True)

        with st.expander("🔍 View Detailed Data Table"):
            st.dataframe(
                filtered[
                    [
                        "name",
                        "averageRating",
                        "priceRange",
                        "asapDeliveryAvailable",
                        "asapPickupAvailable",
                        "asapDeliveryTimeMinutes",
                        "asapPickupMinutes",
                        "displayAddress",
                    ]
                ]
            )
    else:
        st.info("No data found for the selected filter combination.")

    # =========================
    # FOOTER
    # =========================
    st.markdown("---")
    st.subheader("Key Insights")
    st.markdown(
        """
- **Location & Quality Screening**: The map helps identify restaurant clusters and compare quality (ratings) across areas.  
- **Service Efficiency**: Delivery and pickup time filters support faster and more practical choices based on urgency.  
- **Service Availability**: Side-by-side pickup vs delivery charts show how common each option is within the filtered results.  
- **Price Segmentation**: The price distribution highlights which market segment dominates the selected results (Budget–Luxury).  
"""
    )

    st.markdown("**Final Project – Interactive Visualization (Advanced Data Visualization)**")
    st.markdown("Dwina Sarah Delva - 203012410024  \nNadya Arda Anggraini - 203012410016")

except Exception as e:
    st.error(f"An error occurred: {e}")

import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Houston Restaurant Explorer")

# ✅ TAMBAHAN: Inject CSS (sesuai "KODE YANG INGIN DITAMBAHKAN")
st.markdown("""        
<style>
.main { background-color: #f8fafc; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #4f46e5, #4338ca);
    padding: 20px;
}

[data-testid="stSidebar"] * { color: white; }

.stButton > button {
    width: 100%;
    border-radius: 14px;
    padding: 12px;
    font-weight: 600;
    background: rgba(255,255,255,0.18);
    border: none;
    transition: 0.3s;
}

.stButton > button:hover {
    background: rgba(255,255,255,0.35);
    transform: translateY(-2px);
}

.card {
    background: white;
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.kpi {
    background: linear-gradient(135deg, #6366f1, #818cf8);
    color: white;
    border-radius: 18px;
    padding: 20px;
    text-align: center;
}

.kpi h2 { margin: 0; font-size: 30px; }
.kpi p { opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# 2. Fungsi Load Data
@st.cache_data
def load_data():
    # Menggunakan on_bad_lines='skip' karena ada beberapa baris tidak rapi di CSV
    df = pd.read_csv('restaurants.csv', on_bad_lines='skip')
    
    # --- TRANSFORMASI DATA ---
    price_mapping = {'$': 'Murah', '$$': 'Sedang', '$$$': 'Mahal', '$$$$': 'Sangat Mahal'}
    df['priceRange'] = df['priceRange'].map(price_mapping)
    
    bool_mapping = {True: 'Iya', False: 'Tidak'}
    df['asapPickupAvailable'] = df['asapPickupAvailable'].map(bool_mapping)

    # --- TAMBAHAN: Delivery Available ---
    df['asapDeliveryAvailable'] = df['asapDeliveryAvailable'].map(bool_mapping)
    
    # Membersihkan data koordinat dan numerik
    df = df.dropna(subset=['latitude', 'longitude'])
    df['averageRating'] = pd.to_numeric(df['averageRating'], errors='coerce')
    df['asapDeliveryTimeMinutes'] = pd.to_numeric(df['asapDeliveryTimeMinutes'], errors='coerce')
    df['asapPickupMinutes'] = pd.to_numeric(df['asapPickupMinutes'], errors='coerce')
    
    return df

try:
    data = load_data()

    st.title("Houston Restaurant Interactive Explorer")
    st.markdown("Eksplorasi persebaran dan statistik restoran dengan filter rating maksimal.")

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Pencarian")
    search_query = st.sidebar.text_input("Cari Nama Restoran", "")
    
    # Filter Harga
    price_order = ['Murah', 'Sedang', 'Mahal', 'Sangat Mahal']
    available_prices = [p for p in price_order if p in data['priceRange'].unique()]
    selected_price = st.sidebar.multiselect("Kategori Harga", available_prices, default=available_prices)

    # --- Rating Maksimal ---
    max_rating = st.sidebar.slider("Rating Maksimal", 0.0, 5.0, 5.0, 0.1)
    
    # Filter Waktu Pengiriman
    max_del_time = int(data['asapDeliveryTimeMinutes'].max())
    selected_del_time = st.sidebar.slider("Maksimum Waktu Kirim (Menit)", 0, max_del_time, max_del_time)

    # Filter Waktu Pickup
    max_pick_time = int(data['asapPickupMinutes'].max())
    selected_pick_time = st.sidebar.slider("Maksimum Waktu Pickup (Menit)", 0, max_pick_time, max_pick_time)
    
    # Filter Ketersediaan Pickup
    selected_pickup = st.sidebar.selectbox("Tersedia Layanan Pickup?", ['Semua', 'Iya', 'Tidak'])

    # --- TAMBAHAN: Filter Ketersediaan Delivery ---
    selected_delivery = st.sidebar.selectbox("Tersedia Layanan Delivery?", ['Semua', 'Iya', 'Tidak'])
    
    # Pilih Ukuran Titik Peta
    map_measure = st.sidebar.selectbox("Ukuran Titik Peta Berdasarkan:", ["Rating Restoran", "Waktu Pengiriman", "Waktu Pickup"])

    # --- PROSES FILTERING ---
    mask = (
        (data['averageRating'] <= max_rating) &  # Maksimal
        (data['priceRange'].isin(selected_price)) &
        (data['asapDeliveryTimeMinutes'] <= selected_del_time) &
        (data['asapPickupMinutes'] <= selected_pick_time)
    )

    if selected_pickup != 'Semua':
        mask = mask & (data['asapPickupAvailable'] == selected_pickup)

    # --- TAMBAHAN: kondisi filter delivery ---
    if selected_delivery != 'Semua':
        mask = mask & (data['asapDeliveryAvailable'] == selected_delivery)

    if search_query:
        mask = mask & (data['name'].str.contains(search_query, case=False))
        
    filtered = data[mask]

    # --- BAGIAN 1: PETA (FULL WIDTH) ---
    st.subheader("📍 Peta Lokasi Restoran")
    
    if map_measure == "Rating Restoran":
        radius_calc = "averageRating * 15"
        point_color = "[255, 165, 0, 160]" # Oranye
    elif map_measure == "Waktu Pengiriman":
        radius_calc = "asapDeliveryTimeMinutes * 2"
        point_color = "[0, 200, 100, 160]" # Hijau
    else:
        radius_calc = "asapPickupMinutes * 5"
        point_color = "[0, 100, 255, 160]" # Biru

    st.pydeck_chart(pdk.Deck(
        map_style='light',
        initial_view_state=pdk.ViewState(
            latitude=filtered['latitude'].mean() if not filtered.empty else 29.76,
            longitude=filtered['longitude'].mean() if not filtered.empty else -95.36,
            zoom=11, pitch=30
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=filtered,
                get_position="[longitude, latitude]",
                get_fill_color=point_color,
                get_radius=radius_calc,
                pickable=True,
            ),
        ],
        tooltip={
            "html": (
                "<b>{name}</b><br/>"
                "Rating: {averageRating} ⭐<br/>"
                "Harga: {priceRange}<br/>"
                "Delivery: {asapDeliveryAvailable}<br/>"
                "Pickup: {asapPickupAvailable}"
            )
        }
    ))

    st.divider()

    # --- BAGIAN 2: STATISTIK (DI BAWAH MAP) ---
    st.subheader("📊 Analisis Data Terfilter")

    # 1) KPI (4 kolom) - BARIS PERTAMA
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Restoran Ditemukan", len(filtered))
    k2.metric("Rata-rata Rating", f"{filtered['averageRating'].mean():.2f}" if not filtered.empty else "0")
    k3.metric("Rerata Waktu Kirim", f"{int(filtered['asapDeliveryTimeMinutes'].mean())} mnt" if not filtered.empty else "0")
    k4.metric("Rerata Waktu Pickup", f"{int(filtered['asapPickupMinutes'].mean())} mnt" if not filtered.empty else "0")

    if not filtered.empty:
        st.markdown("---")

        # 2) Ketersediaan Pickup & Delivery - BARIS KEDUA (HORIZONTAL)
        st.write("**Ketersediaan Layanan Pickup & Delivery**")

        pickup_counts = filtered['asapPickupAvailable'].value_counts()
        delivery_counts = filtered['asapDeliveryAvailable'].value_counts()

        # PAKSA horizontal (dua kolom sejajar)
        b1, b2 = st.columns(2)
        with b1:
            st.caption("Pickup")
            st.bar_chart(pickup_counts, use_container_width=True)
        with b2:
            st.caption("Delivery")
            st.bar_chart(delivery_counts, use_container_width=True)

        st.markdown("---")

        # 3) Proporsi Kategori Harga - BARIS KETIGA (FULL WIDTH DI BAWAH)
        st.write("**Proporsi Kategori Harga**")
        price_counts = filtered['priceRange'].value_counts().reset_index()
        price_counts.columns = ['Kategori', 'Jumlah']

        fig_price = px.pie(
            price_counts,
            values='Jumlah',
            names='Kategori',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.4
        )
        fig_price.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_price, use_container_width=True)

        # Tabel tetap sama
        with st.expander("🔍 Lihat Detail Tabel Data"):
            st.dataframe(filtered[['name', 'averageRating', 'priceRange',
                                   'asapDeliveryAvailable', 'asapPickupAvailable',
                                   'asapDeliveryTimeMinutes', 'asapPickupMinutes', 'displayAddress']])

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
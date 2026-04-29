import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# Judul Dashboard
st.title("Dashboard Kualitas Udara")

# Load data
def load_data():
    df = pd.read_csv("dashboard/main_data.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

df = load_data()

# Sidebar 
st.sidebar.header("Filter Stasiun")

selected_stations = st.sidebar.multiselect(
    "Pilih Stasiun",
    options=sorted(df["station"].unique()),
    default=[],
    placeholder="Pilih Stasiun"
)

if not selected_stations:
    filtered_df = df.copy()
else:
    filtered_df = df[
        df["station"].isin(selected_stations)
    ].copy()

# Data preparation
filtered_df["month_period"] = filtered_df["datetime"].dt.to_period("M")

monthly_pm25 = (
    filtered_df.groupby("month_period")["PM2.5"]
    .mean()
    .reset_index()
)

station_pm25 = (
    filtered_df.groupby("station")["PM2.5"]
    .mean()
    .sort_values(ascending=False)
)

def categorize_pollution(pm):
    if pm < 72:
        return "Low"
    elif pm < 76:
        return "Moderate"
    return "High"

filtered_df["pollution_category"] = filtered_df["PM2.5"].apply(categorize_pollution)

pollution_distribution = filtered_df["pollution_category"].value_counts()

# visualisasi 1 (Line Chart)
st.subheader("Trend Rata-rata Bulanan PM2.5 (2013-2017)")

col1, col2, col3 = st.columns(3)

with col1:
    total_months = monthly_pm25.shape[0]
    st.metric("Total Bulan Observasi", value=total_months)

with col2:
    highest_pm25 = round(monthly_pm25['PM2.5'].max(), 2)
    st.metric("PM2.5 Tertinggi", value=highest_pm25)

with col3:
    lowest_pm25 = round(monthly_pm25['PM2.5'].min(), 2)
    st.metric("PM2.5 Terendah", value=lowest_pm25)

fig, ax = plt.subplots(figsize=(12, 8))
ax.set_facecolor('#F9F9F9')

ax.plot(
    monthly_pm25["month_period"].astype(str),
    monthly_pm25["PM2.5"],
    linewidth=2,
    color="steelblue",
    zorder=1
)

ax.scatter(
    monthly_pm25["month_period"].astype(str),
    monthly_pm25["PM2.5"],
    c=monthly_pm25["PM2.5"],
    cmap="RdYlGn_r",
    s=50,
    edgecolors="black",
    zorder=2
)

ax.set_xticks(range(0, len(monthly_pm25), 3))
ax.set_xticklabels(
    monthly_pm25["month_period"].astype(str)[::3],
    rotation=45
)
ax.grid(alpha=0.3)

st.pyplot(fig)

# visualisasi 2 (Horizontal bar plot)
st.subheader("Rata-rata PM2.5 per Stasiun")

fig, ax = plt.subplots(figsize=(6, 6))
ax.set_facecolor("#F9F9F9")

bar_colors = [
    "crimson" if value == station_pm25.max() else "lightgray"
    for value in station_pm25
]

station_pm25.plot(
    kind="barh",
    color=bar_colors,
    ax=ax
)

ax.invert_yaxis()
ax.set_ylabel("")
ax.set_xlabel('PM2.5')
ax.grid(axis="x", alpha=0.3)
st.pyplot(fig)

# visualisasi 3 (Geospasial)
st.subheader(
    "Informasi Stasiun Berdasarkan Letak Geografis dan Level PM2.5"
)

station_coords = {
    "Aotizhongxin": [39.98, 116.39],
    "Changping": [40.22, 116.23],
    "Dingling": [40.29, 116.22],
    "Dongsi": [39.93, 116.42],
    "Guanyuan": [39.93, 116.34],
    "Gucheng": [39.90, 116.22],
    "Huairou": [40.32, 116.63],
    "Nongzhanguan": [39.93, 116.46],
    "Shunyi": [40.12, 116.65],
    "Tiantan": [39.89, 116.41],
    "Wanliu": [39.98, 116.30],
    "Wanshouxigong": [39.87, 116.36]
}

m = folium.Map(
    location=[39.9, 116.4],
    zoom_start=10,
    tiles="CartoDB positron"
)

def get_color(pm):
    if pm < 72:
        return "#2ECC71"
    elif pm < 76:
        return "#F1C40F"
    return "#E74C3C"

for station, pm in station_pm25.items():
    if station in station_coords:
        lat, lon = station_coords[station]

        folium.CircleMarker(
            location=[lat, lon],
            radius=9,
            popup=f"{station}: {pm:.2f}",
            tooltip=station,
            color=get_color(pm),
            fill=True,
            fill_color=get_color(pm),
            fill_opacity=0.8
        ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                icon_size=(150, 36),
                icon_anchor=(0, 0),
                html=f"""
                <div style="
                    font-size: 9px;
                    font-weight: bold;
                    color: black;
                    white-space: nowrap;
                    transform: translate(-15px, 12px);
                ">
                    {station}
                </div>
                """
            )
        ).add_to(m)

legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
background-color: white;
padding: 10px;
border: 1px solid black;
font-size: 14px;
z-index: 9999;
">
<b>PM2.5 Level</b><br>
<span style="color:#2ECC71;">●</span> Low<br>
<span style="color:#F1C40F;">●</span> Moderate<br>
<span style="color:#E74C3C;">●</span> High
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=900, height=900)
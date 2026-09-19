import pandas as pd
import streamlit as st

from queries import latest_per_city, load_gold, risk_color

st.set_page_config(page_title="Meteor · Weather Risk Dashboard", page_icon="🌤️", layout="wide")

st.title("🌤️ Meteor — Weather Risk Dashboard")
st.caption("Gold layer analytics: daily weather risk across Moroccan cities (bronze → silver → gold medallion pipeline).")

df = load_gold()

if df.empty:
    st.warning("No gold data found. Run the pipeline (`bronze` → `silver` → `gold`) first, then reload.")
    st.stop()

cities = sorted(df["city_name"].unique())
min_date, max_date = df["date"].min().date(), df["date"].max().date()
risk_levels = ["LOW", "MODERATE", "HIGH", "EXTREME"]

with st.sidebar:
    st.header("Filters")
    selected_cities = st.multiselect("Cities", cities, default=cities)
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    seasons = sorted(df["season"].dropna().unique().tolist())
    selected_seasons = st.multiselect("Périodes (saison)", seasons, default=seasons)
    selected_levels = st.multiselect("Risk levels", risk_levels, default=risk_levels)
    st.caption(f"Data window: {min_date} → {max_date} · {len(cities)} cities")

if isinstance(date_range, (list, tuple)):
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

mask = df["city_name"].isin(selected_cities)
mask &= df["date"].dt.date >= pd.Timestamp(start_date).date()
mask &= df["date"].dt.date <= pd.Timestamp(end_date).date()
mask &= df["season"].isin(selected_seasons)
mask &= df["risk_level"].isin(selected_levels)
filtered = df[mask].copy()

latest = latest_per_city(filtered)

if filtered.empty:
    st.info("No data matches the selected filters.")
    st.stop()

kpi_cols = st.columns(4)
kpi_cols[0].metric("Records", f"{len(filtered):,}")
kpi_cols[1].metric("Cities", f"{filtered['city_name'].nunique():,}")
kpi_cols[2].metric("Avg risk score", f"{filtered['risk_score'].mean():.1f}" if not filtered.empty else "—")
kpi_cols[3].metric(
    "High + Extreme days",
    f"{((filtered['risk_level'].isin(['HIGH', 'EXTREME'])).sum()):,}" if not filtered.empty else "—",
)

tab_map, tab_trend, tab_risk, tab_data = st.tabs(
    ["🗺️ Map", "📈 Trends", "🎯 Risk analysis", "📋 Data"]
)

with tab_map:
    map_df = latest.copy()
    map_df["color"] = map_df["risk_level"].apply(risk_color)
    map_df["label"] = (map_df["city_name"] + " · " + map_df["risk_score"].astype(str)).str.slice(0, 30)
    st.map(
        map_df,
        latitude="latitude",
        longitude="longitude",
        color="color",
    )
    with st.expander("Latest risk levels per city"):
        st.dataframe(
            latest[["city_name", "date", "risk_score", "risk_level", "temp_category", "precip_category", "wind_category"]]
            .sort_values("risk_score", ascending=False)
            .reset_index(drop=True),
            width="stretch",
        )

with tab_trend:
    col1, col2 = st.columns([1, 2])
    with col1:
        trend_city = st.selectbox("City", cities)
        trend_metric = st.radio("Metric", ["risk_score", "temp_max_celsius", "precipitation_mm"], horizontal=True)
    city_df = (
        filtered[filtered["city_name"] == trend_city]
        .set_index("date")[[trend_metric]]
        .sort_index()
    )
    with col2:
        if not city_df.empty:
            st.line_chart(city_df)
            latest_risk = city_df["risk_score"].iloc[-1]
            st.caption(f"Latest {trend_metric} for {trend_city}: **{latest_risk:g}**")
        else:
            st.info("No data for the selected city in this filter window.")

with tab_risk:
    dist = pd.DataFrame(
        {lvl: [filtered["risk_level"].eq(lvl).sum()] for lvl in risk_levels}
    )
    bar_colors = [risk_color(lvl) for lvl in risk_levels]
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Risk level distribution")
        st.bar_chart(dist, color=bar_colors)
    with col_b:
        st.subheader("Top 10 riskiest cities")
        top = (
            filtered.groupby("city_name")["risk_score"]
            .max()
            .sort_values(ascending=False)
            .head(10)
        )
        st.bar_chart(top, color=[risk_color("HIGH")])
        st.caption("Highest single-day risk score per city.")

with tab_data:
    st.subheader("Daily weather summary — gold layer")
    export_cols = [
        "city_name", "date", "temp_max_celsius", "temp_min_celsius",
        "precipitation_mm", "temp_category", "precip_category",
        "wind_category", "season", "risk_score", "risk_level",
    ]
    st.dataframe(filtered[export_cols], width="stretch")
    st.download_button(
        "Download CSV",
        filtered[export_cols].to_csv(index=False).encode("utf-8"),
        file_name="meteor_gold_summary.csv",
        mime="text/csv",
    )
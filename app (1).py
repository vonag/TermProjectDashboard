import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Gender Gap in Education",
    layout="wide",
)

st.title("The Gender Gap in Education (1990 to 2023)")

# -----------------------------
# How-to callout
# -----------------------------
with st.expander("How to use this dashboard", expanded=True):
    st.markdown(
        """
        - **Pick one or more countries** in the sidebar to compare them on the same chart.
        - **Use the year range slider** in the sidebar to limit the overall time period.
        - **Click and drag on the top chart** to select a shorter window of years.
          The gap chart below will zoom into exactly that window, and the selected range will show above it.
        - **Hover over any line or bar** to see exact values.
        """
    )

# -----------------------------
# Load and prep data
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("schooling_data.csv")
    long_df = df.melt(
        id_vars=["Entity", "Code", "Year"],
        value_vars=["Girls", "Boys"],
        var_name="Gender",
        value_name="Years of Schooling",
    )
    df["Gap (Boys - Girls)"] = df["Boys"] - df["Girls"]
    return df, long_df

df, long_df = load_data()

countries = sorted(df["Entity"].unique())
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Explore the data")

# Multiselect for comparison mode
default_countries = [c for c in ["United States", "Iran"] if c in countries]
selected_countries = st.sidebar.multiselect(
    "Countries (pick one or more)",
    options=countries,
    default=default_countries if default_countries else countries[:2],
)

if not selected_countries:
    st.warning("Please select at least one country in the sidebar.")
    st.stop()

year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

# -----------------------------
# Filter data
# -----------------------------
filtered_df = df[
    (df["Entity"].isin(selected_countries))
    & (df["Year"] >= year_range[0])
    & (df["Year"] <= year_range[1])
]
filtered_long = long_df[
    (long_df["Entity"].isin(selected_countries))
    & (long_df["Year"] >= year_range[0])
    & (long_df["Year"] <= year_range[1])
]

# -----------------------------
# Brush selection
# -----------------------------
brush = alt.selection_interval(encodings=["x"])

# -----------------------------
# Trend chart with brush
# -----------------------------
trend = alt.Chart(filtered_long).mark_line(point=True).encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y("Years of Schooling:Q", title="Years of Schooling"),
    color=alt.Color("Entity:N", title="Country"),
    strokeDash=alt.StrokeDash("Gender:N", title="Gender"),
    tooltip=["Entity", "Year", "Gender", "Years of Schooling"],
).properties(
    height=300,
    title="Years of Schooling Over Time",
).add_params(brush)

# -----------------------------
# Brush range label
# -----------------------------
brush_label = alt.Chart(filtered_df).transform_filter(
    brush
).transform_aggregate(
    min_year="min(Year)",
    max_year="max(Year)",
).transform_calculate(
    label='"Selected years: " + datum.min_year + " to " + datum.max_year'
).mark_text(
    align="left",
    baseline="top",
    fontSize=14,
    fontWeight="bold",
    color="#333",
).encode(
    text="label:N",
    x=alt.value(10),
    y=alt.value(5),
).properties(height=30)

# -----------------------------
# Gap chart (filtered by brush)
# -----------------------------
gap = alt.Chart(filtered_df).mark_bar().encode(
    x=alt.X("Year:O", title="Year"),
    xOffset=alt.XOffset("Entity:N"),
    y=alt.Y("Gap (Boys - Girls):Q", title="Gap (Boys minus Girls), in years"),
    color=alt.Color("Entity:N", title="Country"),
    tooltip=["Entity", "Year", "Gap (Boys - Girls)"],
).properties(
    height=250,
    title="Gender Gap (Boys minus Girls). Positive values mean boys received more schooling.",
).transform_filter(brush)

# -----------------------------
# Combine all three into one spec
# -----------------------------
chart = alt.vconcat(trend, brush_label, gap).resolve_scale(color="shared")

st.altair_chart(chart, use_container_width=True)

# -----------------------------
# Metrics per country
# -----------------------------
st.subheader("Current gap by country (most recent year in range)")

latest_year = filtered_df["Year"].max()
cols = st.columns(len(selected_countries))
for i, country in enumerate(selected_countries):
    country_data = filtered_df[
        (filtered_df["Entity"] == country) & (filtered_df["Year"] == latest_year)
    ]
    if not country_data.empty:
        gap_value = country_data["Gap (Boys - Girls)"].iloc[0]
        cols[i].metric(
            label=f"{country} ({latest_year})",
            value=f"{gap_value:.2f} years",
        )

import streamlit as st
import pandas as pd
import altair as alt

# Load data
df = pd.read_csv("average-years-of-schooling-among-men-and-women.csv")

# Long format for the line chart
long_df = df.melt(
    id_vars=["Entity", "Code", "Year"],
    value_vars=["Girls", "Boys"],
    var_name="Gender",
    value_name="Years of Schooling",
)

# Add gap column for the bar chart
df["Gap (Boys - Girls)"] = df["Boys"] - df["Girls"]

# Sidebar controls
countries = sorted(df["Entity"].unique())
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())

st.title("The Gender Gap in Education, 1990–2023")
st.markdown("Pick a country and year range, then drag across the top chart to zoom into a time window.")

country = st.sidebar.selectbox("Country", countries)
year_range = st.sidebar.slider("Year range", min_year, max_year, (min_year, max_year))

# Filter data
filtered_long = long_df[
    (long_df["Entity"] == country)
    & (long_df["Year"] >= year_range[0])
    & (long_df["Year"] <= year_range[1])
]
filtered_wide = df[
    (df["Entity"] == country)
    & (df["Year"] >= year_range[0])
    & (df["Year"] <= year_range[1])
]

# Brush selection (within-viz interaction)
brush = alt.selection_interval(encodings=["x"])

# Chart A: trend line
line_chart = alt.Chart(filtered_long).mark_line(point=True).encode(
    x=alt.X("Year:Q", axis=alt.Axis(format="d")),
    y="Years of Schooling:Q",
    color="Gender:N",
    tooltip=["Gender", "Year", "Years of Schooling"]
).add_params(brush).properties(title=f"Average years of schooling — {country}")

# Chart B: gap chart, coordinated with the brush
gap_chart = alt.Chart(filtered_wide).mark_bar().encode(
    x=alt.X("Year:Q", axis=alt.Axis(format="d")),
    y="Gap (Boys - Girls):Q",
    tooltip=["Year", "Girls", "Boys", "Gap (Boys - Girls)"]
).transform_filter(brush).properties(title="Gender gap in selected window")

# Display
combined_chart = alt.vconcat(line_chart, gap_chart).resolve_scale(
    color='independent'
)
st.altair_chart(combined_chart, use_container_width=True)
st.caption("Drag across the chart above to select a time range.")

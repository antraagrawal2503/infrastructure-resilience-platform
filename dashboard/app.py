from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st
import pydeck as pdk


DATA_FILE = Path("data/processed/brisbane_roads_priority.gpkg")


st.set_page_config(
    page_title="Brisbane Infrastructure Resilience Dashboard",
    page_icon="🛣️",
    layout="wide",
)


@st.cache_data
def load_data():
    return gpd.read_file(
        DATA_FILE,
        layer="brisbane_roads_priority"
    )


roads = load_data()


# -------------------------
# HEADER
# -------------------------

st.title("Brisbane Infrastructure Resilience Dashboard")

st.caption(
    "Decision-support dashboard for analysing flood exposure, "
    "infrastructure risk and road prioritisation across Brisbane."
)


# -------------------------
# SIDEBAR FILTERS
# -------------------------

st.sidebar.header("Filters")


priority_options = [
    "Low",
    "Moderate",
    "High",
    "Critical"
]

selected_priorities = st.sidebar.multiselect(
    "Priority level",
    priority_options,
    default=priority_options
)


flood_options = [
    "None",
    "Very Low",
    "Low",
    "Medium",
    "High"
]

selected_flood = st.sidebar.multiselect(
    "Flood exposure",
    flood_options,
    default=flood_options
)


road_classes = sorted(
    roads["class"]
    .dropna()
    .unique()
    .tolist()
)

selected_classes = st.sidebar.multiselect(
    "Road class",
    road_classes,
    default=road_classes
)


filtered = roads[
    roads["priority"].isin(selected_priorities)
    & roads["flood_exposure"].isin(selected_flood)
    & roads["class"].isin(selected_classes)
].copy()


# -------------------------
# KPIs
# -------------------------

total_segments = len(filtered)

flood_exposed = (
    filtered["flood_exposure"] != "None"
).sum()

medium_high = filtered[
    "flood_exposure"
].isin(
    ["Medium", "High"]
).sum()

critical_segments = (
    filtered["priority"] == "Critical"
).sum()


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Road Segments",
    f"{total_segments:,}"
)

col2.metric(
    "Flood Exposed",
    f"{flood_exposed:,}"
)

col3.metric(
    "Medium / High Exposure",
    f"{medium_high:,}"
)

col4.metric(
    "Critical Priority",
    f"{critical_segments:,}"
)


st.divider()


# -------------------------
# PRIORITY DISTRIBUTION
# -------------------------

left, right = st.columns(2)


with left:

    st.subheader("Priority Distribution")

    priority_counts = (
        filtered["priority"]
        .value_counts()
        .reindex(
            [
                "Low",
                "Moderate",
                "High",
                "Critical",
            ],
            fill_value=0
        )
    )

    st.bar_chart(priority_counts)


with right:

    st.subheader("Flood Exposure Distribution")

    flood_counts = (
        filtered["flood_exposure"]
        .value_counts()
        .reindex(
            [
                "None",
                "Very Low",
                "Low",
                "Medium",
                "High",
            ],
            fill_value=0
        )
    )

    st.bar_chart(flood_counts)


st.divider()

# -------------------------
# INTERACTIVE RISK MAP
# -------------------------

st.subheader("Interactive Infrastructure Risk Map")

st.caption(
    "Explore Brisbane road segments by infrastructure priority. "
    "Hover over a segment to view its risk information."
)


# PyDeck expects WGS84 longitude/latitude coordinates
map_roads = filtered.to_crs(epsg=4326).copy()

# Remove empty geometries
map_roads = map_roads[
    map_roads.geometry.notna()
    & ~map_roads.geometry.is_empty
].copy()


# Colours used for each priority level
priority_colours = {
    "Low": [76, 175, 80, 90],
    "Moderate": [255, 193, 7, 150],
    "High": [255, 87, 34, 190],
    "Critical": [183, 28, 28, 230],
}

map_roads["colour"] = map_roads["priority"].map(
    priority_colours
)


# Convert LineString / MultiLineString geometry
# into coordinate arrays for PyDeck
def geometry_to_paths(geometry):

    if geometry.geom_type == "LineString":
        return [list(geometry.coords)]

    if geometry.geom_type == "MultiLineString":
        return [
            list(line.coords)
            for line in geometry.geoms
        ]

    return []


map_roads["paths"] = map_roads.geometry.apply(
    geometry_to_paths
)


# One row per drawable road path
map_data = map_roads[
    [
        "road_name_full",
        "class",
        "sub_class",
        "flood_exposure",
        "risk_score",
        "priority",
        "colour",
        "paths",
    ]
].explode("paths")


map_data = map_data[
    map_data["paths"].notna()
]


if not map_data.empty:

    road_layer = pdk.Layer(
        "PathLayer",
        data=map_data,
        get_path="paths",
        get_color="colour",
        get_width=3,
        width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=-27.47,
        longitude=153.03,
        zoom=9.5,
        pitch=0,
    )

    tooltip = {
        "html": """
        <b>{road_name_full}</b><br/>
        Road Class: {class}<br/>
        Infrastructure: {sub_class}<br/>
        Flood Exposure: {flood_exposure}<br/>
        Risk Score: {risk_score}<br/>
        Priority: {priority}
        """
    }

    deck = pdk.Deck(
        layers=[road_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None,
    )

    st.pydeck_chart(
        deck,
        use_container_width=True
    )

else:

    st.info(
        "No road segments match the selected filters."
    )


st.divider()


# -------------------------
# TOP PRIORITY ROADS
# -------------------------

st.subheader("Top Priority Roads")

st.caption(
    "Road-level summary ranked by maximum risk score and exposure severity."
)

named_roads = filtered[
    filtered["road_name_full"].notna()
    & (filtered["road_name_full"].str.strip() != "")
].copy()

road_summary = (
    named_roads
    .groupby("road_name_full")
    .agg(
        road_class=(
            "class",
            lambda x: x.mode().iloc[0]
            if not x.mode().empty
            else "Unknown"
        ),
        max_risk_score=("risk_score", "max"),
        mean_risk_score=("risk_score", "mean"),
        total_segments=("segment_id", "count"),
        exposed_segments=(
            "flood_exposure",
            lambda x: (x != "None").sum()
        ),
        high_exposure_segments=(
            "flood_exposure",
            lambda x: x.isin(
                ["Medium", "High"]
            ).sum()
        ),
        critical_segments=(
            "priority",
            lambda x: (x == "Critical").sum()
        ),
    )
    .reset_index()
)

road_summary = road_summary.sort_values(
    [
        "max_risk_score",
        "high_exposure_segments",
        "exposed_segments",
    ],
    ascending=[False, False, False],
)

top_roads = road_summary.head(20).copy()

top_roads["mean_risk_score"] = (
    top_roads["mean_risk_score"]
    .round(1)
)

top_roads = top_roads.rename(
    columns={
        "road_name_full": "Road",
        "road_class": "Road Class",
        "max_risk_score": "Max Risk Score",
        "mean_risk_score": "Mean Risk Score",
        "total_segments": "Segments",
        "exposed_segments": "Flood Exposed",
        "high_exposure_segments": "Medium / High Exposure",
        "critical_segments": "Critical Segments",
    }
)

st.dataframe(
    top_roads,
    width="stretch",
    hide_index=True
)
from pathlib import Path

import geopandas as gpd
import pandas as pd


INPUT_FILE = Path("data/processed/brisbane_roads_flood_risk.gpkg")
OUTPUT_FILE = Path("data/processed/brisbane_roads_priority.gpkg")


# Maximum 50 points
FLOOD_SCORES = {
    "None": 0,
    "Very Low": 10,
    "Low": 20,
    "Medium": 35,
    "High": 50,
}

# Maximum 30 points
ROAD_CLASS_SCORES = {
    "Motorway": 30,
    "Highway": 30,
    "Busway": 25,
    "Secondary": 20,
    "Connector": 15,
    "Local": 10,
    "Restricted": 5,
    "Track": 5,
    "Bikeway": 5,
    "Walkway": 5,
    "Mall": 5,
    "Ferry": 5,
}

# Maximum 20 points
INFRASTRUCTURE_SCORES = {
    "Bridge": 20,
    "Tunnel": 20,
    "Causeway": 20,
    "Level Crossing": 15,
    "Ramp": 10,
    "Slip": 10,
    "Roundabout": 5,
}


def priority_category(score):
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Moderate"
    return "Low"


def main():
    print("Loading flood-risk road dataset...")

    roads = gpd.read_file(INPUT_FILE)

    print(f"Loaded {len(roads):,} road segments.")

    # Calculate individual score components
    roads["flood_score"] = (
        roads["flood_exposure"]
        .map(FLOOD_SCORES)
        .fillna(0)
    )

    roads["importance_score"] = (
        roads["class"]
        .map(ROAD_CLASS_SCORES)
        .fillna(0)
    )

    roads["infrastructure_score"] = (
        roads["sub_class"]
        .map(INFRASTRUCTURE_SCORES)
        .fillna(0)
    )

    # Total score: 0–100
    roads["risk_score"] = (
        roads["flood_score"]
        + roads["importance_score"]
        + roads["infrastructure_score"]
    )

    roads["priority"] = roads["risk_score"].apply(priority_category)

    print("\nPriority distribution:")
    print(roads["priority"].value_counts())

    print("\nRisk-score statistics:")
    print(roads["risk_score"].describe())

    # Show useful columns for highest-priority segments
    display_columns = [
        "road_name_full",
        "class",
        "sub_class",
        "flood_exposure",
        "flood_score",
        "importance_score",
        "infrastructure_score",
        "risk_score",
        "priority",
    ]

    top_roads = (
        roads.sort_values("risk_score", ascending=False)
        [display_columns]
        .head(20)
    )

    print("\nTop 20 priority road segments:")
    print(top_roads.to_string(index=False))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    roads.to_file(
        OUTPUT_FILE,
        layer="brisbane_roads_priority",
        driver="GPKG",
    )

    # Also save a small recruiter/dashboard-friendly table
    top_roads.to_csv(
        "data/processed/top_priority_roads.csv",
        index=False,
    )

    print(f"\nSaved priority dataset to {OUTPUT_FILE}")
    print("Saved Top 20 table to data/processed/top_priority_roads.csv")


if __name__ == "__main__":
    main()
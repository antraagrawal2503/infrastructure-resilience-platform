from pathlib import Path

import geopandas as gpd
import pandas as pd


INPUT_FILE = Path("data/processed/brisbane_roads_priority.gpkg")
OUTPUT_FILE = Path("data/processed/road_priority_summary.csv")


def main():
    print("Loading priority dataset...")

    roads = gpd.read_file(
        INPUT_FILE,
        layer="brisbane_roads_priority"
    )

    print(f"Loaded {len(roads):,} road segments.")

    # Remove unnamed roads from named-road ranking
    named = roads[
        roads["road_name_full"].notna()
        & (roads["road_name_full"].str.strip() != "")
    ].copy()

    # Summarise multiple segments belonging to the same road
    summary = (
        named.groupby("road_name_full")
        .agg(
            max_risk_score=("risk_score", "max"),
            mean_risk_score=("risk_score", "mean"),
            total_segments=("segment_id", "count"),
            exposed_segments=(
                "flood_exposure",
                lambda x: (x != "None").sum()
            ),
            high_exposure_segments=(
                "flood_exposure",
                lambda x: x.isin(["High", "Medium"]).sum()
            ),
            road_class=("class", lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown"),
        )
        .reset_index()
    )

    # Rank primarily by maximum infrastructure risk,
    # then by how much of the road is exposed.
    summary = summary.sort_values(
        ["max_risk_score", "high_exposure_segments", "exposed_segments"],
        ascending=[False, False, False],
    )

    summary["rank"] = range(1, len(summary) + 1)

    # Put rank first
    columns = [
        "rank",
        "road_name_full",
        "road_class",
        "max_risk_score",
        "mean_risk_score",
        "total_segments",
        "exposed_segments",
        "high_exposure_segments",
    ]

    summary = summary[columns]

    print("\nTop 20 priority roads:\n")

    print(
        summary.head(20).to_string(
            index=False,
            formatters={
                "mean_risk_score": "{:.1f}".format
            }
        )
    )

    summary.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved road summary to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
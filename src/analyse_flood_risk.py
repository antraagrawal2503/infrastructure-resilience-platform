import geopandas as gpd
from pathlib import Path


ROADS_FILE = Path("data/processed/brisbane_roads.gpkg")
FLOOD_FILE = Path("data/raw/flood-awareness-flood-risk-overall.geojson")

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "brisbane_roads_flood_risk.gpkg"

RISK_SCORES = {
    "Very Low": 1,
    "Low": 2,
    "Medium": 3,
    "High": 4,
}


def load_data():
    print("Loading Brisbane roads...")
    roads = gpd.read_file(
        ROADS_FILE,
        layer="brisbane_roads"
    )

    print(f"Loaded {len(roads):,} road segments.")

    print("Loading flood-risk polygons...")
    flood = gpd.read_file(FLOOD_FILE)

    print(f"Loaded {len(flood):,} flood polygons.")

    return roads, flood


def prepare_flood_data(flood):
    """Keep only fields needed for flood exposure analysis."""

    flood = flood[
        [
            "flood_risk",
            "geometry",
        ]
    ].copy()

    flood["flood_score"] = flood["flood_risk"].map(RISK_SCORES)

    return flood


def align_coordinate_systems(roads, flood):
    """Ensure both datasets use the same coordinate reference system."""

    print(f"Road CRS: {roads.crs}")
    print(f"Flood CRS: {flood.crs}")

    if roads.crs != flood.crs:
        print("Converting flood data to road CRS...")
        flood = flood.to_crs(roads.crs)

    return roads, flood


def calculate_flood_exposure(roads, flood):
    """
    Match roads with flood polygons they intersect.

    A road may intersect several polygons.
    We retain the highest flood-risk score affecting each road segment.
    """

    print("Running spatial intersection...")

    joined = gpd.sjoin(
        roads,
        flood,
        how="left",
        predicate="intersects"
    )

    print(f"Spatial join produced {len(joined):,} matches.")

    exposure = (
        joined
        .groupby("segment_id", as_index=False)
        .agg(
            flood_score=("flood_score", "max")
        )
    )

    roads = roads.merge(
        exposure,
        on="segment_id",
        how="left"
    )

    roads["flood_score"] = roads["flood_score"].fillna(0).astype(int)

    score_to_label = {
        0: "None",
        1: "Very Low",
        2: "Low",
        3: "Medium",
        4: "High",
    }

    roads["flood_exposure"] = roads["flood_score"].map(score_to_label)

    return roads


def print_summary(roads):
    print("\nFlood exposure summary:")
    print(
        roads["flood_exposure"]
        .value_counts()
        .reindex(
            ["None", "Very Low", "Low", "Medium", "High"],
            fill_value=0
        )
    )

    exposed = (roads["flood_score"] > 0).sum()

    print(
        f"\nFlood-exposed road segments: "
        f"{exposed:,} / {len(roads):,}"
    )


def save_results(roads):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    roads.to_file(
        OUTPUT_FILE,
        layer="brisbane_roads_flood_risk",
        driver="GPKG"
    )

    print(f"\nSaved results to {OUTPUT_FILE}")


def main():
    roads, flood = load_data()

    flood = prepare_flood_data(flood)

    roads, flood = align_coordinate_systems(
        roads,
        flood
    )

    roads = calculate_flood_exposure(
        roads,
        flood
    )

    print_summary(roads)

    save_results(roads)


if __name__ == "__main__":
    main()
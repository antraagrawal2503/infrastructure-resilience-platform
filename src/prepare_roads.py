import geopandas as gpd
from pathlib import Path


RAW_DATA = Path("data/raw/data.gdb")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "brisbane_roads.gpkg"

LAYER = "Queensland_roads_and_tracks"


def load_roads():
    """Load the Queensland Roads and Tracks dataset."""
    print("Loading Queensland road data...")

    roads = gpd.read_file(RAW_DATA, layer=LAYER)

    print(f"Loaded {len(roads):,} road segments.")
    return roads


def filter_brisbane(roads):
    """Keep road segments associated with Brisbane."""

    brisbane = roads[
        roads["lga_name_left"].fillna("").str.contains("Brisbane", case=False)
        | roads["lga_name_right"].fillna("").str.contains("Brisbane", case=False)
    ].copy()

    print(f"Brisbane road segments: {len(brisbane):,}")
    return brisbane


def select_columns(roads):
    """Keep attributes useful for infrastructure analysis."""

    columns = [
        "road_name_full",
        "class",
        "road_id",
        "segment_id",
        "sub_class",
        "surface_type",
        "op_status_ind",
        "user_access",
        "travel_direction",
        "lane_count",
        "trafficability",
        "seasonality",
        "road_owner",
        "road_maintainer",
        "locality_left",
        "locality_right",
        "lga_name_left",
        "lga_name_right",
        "last_edited_date",
        "geometry",
    ]

    return roads[columns].copy()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    roads = load_roads()
    roads = filter_brisbane(roads)
    roads = select_columns(roads)

    roads.to_file(
        OUTPUT_FILE,
        layer="brisbane_roads",
        driver="GPKG"
    )

    print(f"Saved processed dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
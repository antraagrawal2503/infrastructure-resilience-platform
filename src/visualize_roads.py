import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path


DATA_FILE = Path("data/processed/brisbane_roads.gpkg")
OUTPUT_DIR = Path("docs/images")
OUTPUT_FILE = OUTPUT_DIR / "brisbane_road_network.png"


def main():
    print("Loading Brisbane road network...")

    roads = gpd.read_file(
        DATA_FILE,
        layer="brisbane_roads"
    )

    print(f"Loaded {len(roads):,} road segments.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 12))

    roads.plot(
        ax=ax,
        linewidth=0.25
    )

    ax.set_title(
        "Brisbane Road Infrastructure Network",
        fontsize=16
    )

    ax.set_axis_off()

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Map saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
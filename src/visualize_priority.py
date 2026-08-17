from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt


INPUT_FILE = Path("data/processed/brisbane_roads_priority.gpkg")
OUTPUT_DIR = Path("docs/images")
OUTPUT_FILE = OUTPUT_DIR / "brisbane_infrastructure_priority.png"


def main():
    print("Loading infrastructure priority dataset...")

    roads = gpd.read_file(
        INPUT_FILE,
        layer="brisbane_roads_priority"
    )

    print(f"Loaded {len(roads):,} road segments.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Focus on main Brisbane metro extent
    roads = roads.cx[152.85:153.25, -27.75:-27.20]

    fig, ax = plt.subplots(figsize=(12, 10))

    # Background network
    low = roads[roads["priority"] == "Low"]

    low.plot(
        ax=ax,
        linewidth=0.25,
        alpha=0.25
    )

    # Higher priorities
    for priority, width in [
        ("Moderate", 0.5),
        ("High", 0.8),
        ("Critical", 1.3),
    ]:
        subset = roads[roads["priority"] == priority]

        subset.plot(
            ax=ax,
            linewidth=width,
            label=priority
        )

    ax.set_title(
        "Brisbane Infrastructure Priority Map",
        fontsize=17,
        fontweight="bold",
        pad=15
    )

    ax.legend(
        title="Priority Level",
        loc="lower left"
    )

    ax.set_axis_off()

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Priority map saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
    
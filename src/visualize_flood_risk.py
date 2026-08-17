import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
from shapely.geometry import box


DATA_FILE = Path("data/processed/brisbane_roads_flood_risk.gpkg")
OUTPUT_DIR = Path("docs/images")
OUTPUT_FILE = OUTPUT_DIR / "brisbane_flood_risk_roads.png"


def main():
    print("Loading flood-risk road data...")

    roads = gpd.read_file(
        DATA_FILE,
        layer="brisbane_roads_flood_risk"
    )

    print(f"Loaded {len(roads):,} road segments.")

    # Remove geometry outside the main Brisbane metropolitan view
    from shapely.geometry import box

    brisbane_bbox = box(
        152.85,   # west
        -27.75,   # south
        153.25,   # east
        -27.20    # north
    )

    roads = gpd.clip(roads, brisbane_bbox)
    

    print(f"Road segments inside map extent: {len(roads):,}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 10))

    # Background road network
    background = roads[roads["flood_score"] == 0]

    background.plot(
        ax=ax,
        color="lightgrey",
        linewidth=0.25,
        alpha=0.45
    )

    # Plot exposed roads by severity
    risk_styles = {
        1: ("#fee8c8", 0.5),
        2: ("#fdbb84", 0.7),
        3: ("#e34a33", 0.9),
        4: ("#7f0000", 1.2),
    }

    labels = {
        1: "Very Low",
        2: "Low",
        3: "Medium",
        4: "High",
    }

    for score, (colour, width) in risk_styles.items():

        subset = roads[roads["flood_score"] == score]

        subset.plot(
            ax=ax,
            color=colour,
            linewidth=width,
            alpha=0.9
        )

    ax.set_title(
        "Brisbane Road Network — Flood Exposure",
        fontsize=17,
        fontweight="bold",
        pad=15
    )

    ax.text(
        0.5,
        1.01,
        "Road segments classified by maximum intersecting flood-risk level",
        transform=ax.transAxes,
        ha="center",
        fontsize=10
    )

    legend_elements = [
        Line2D([0], [0], color="lightgrey", lw=2, label="No identified exposure"),
        Line2D([0], [0], color="#fee8c8", lw=3, label="Very Low"),
        Line2D([0], [0], color="#fdbb84", lw=3, label="Low"),
        Line2D([0], [0], color="#e34a33", lw=3, label="Medium"),
        Line2D([0], [0], color="#7f0000", lw=3, label="High"),
    ]

    ax.legend(
        handles=legend_elements,
        title="Flood Exposure",
        loc="lower left",
        frameon=True
    )

    ax.set_axis_off()

    plt.tight_layout()

    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Improved flood-risk map saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
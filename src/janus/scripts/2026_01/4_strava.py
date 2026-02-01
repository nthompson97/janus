from pathlib import Path

import contextily as cx
import gpxpy
import matplotlib.pyplot as plt
import numpy as np
from pyproj import Transformer


RAW_PATH = Path("/data/raw")
OUT_PATH = Path("/data/images")

DAYS: int = 30
WINDOW: int = 5  # Total days to show (2 before + current + 2 after)

# Image dimensions (wide and short - bottom half of landscape A4)
HORIZONTAL_PX = 2400
VERTICAL_PX = 800  # ~3:1 aspect ratio
DPI = 150

# Route styling
CURRENT_DAY_COLOR = "#E63946"  # Bold red for current day
CURRENT_DAY_WIDTH = 2

CONTEXT_DAY_COLOR = "#1D3557"  # Darker blue for context days
CONTEXT_DAY_WIDTH = 1
CONTEXT_DAY_ALPHA = 0.8
CONTEXT_DAY_STYLE = "--"  # Dashed line for context days

# Map padding (fraction of route extent to add as margin)
MAP_PADDING = 0.1


def load_gpx_coordinates(gpx_path: Path) -> tuple[list[float], list[float]]:
    """Load a GPX file and return lists of latitudes and longitudes."""
    with open(gpx_path, "r") as f:
        gpx = gpxpy.parse(f)

    lats = []
    lons = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                lats.append(point.latitude)
                lons.append(point.longitude)

    return lats, lons


def convert_to_web_mercator(
    lats: list[float],
    lons: list[float],
) -> tuple[np.ndarray, np.ndarray]:
    """Convert lat/lon to Web Mercator (EPSG:3857) for use with contextily tiles."""
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    xs, ys = transformer.transform(lons, lats)
    return np.array(xs), np.array(ys)


def get_window_days(current_day: int, total_days: int, window_size: int) -> list[int]:
    """
    Get the list of days to display for a given current day.
    Centers the window around current_day, clamping to valid range.
    """
    half_window = window_size // 2

    # Calculate ideal window bounds
    start = current_day - half_window
    end = current_day + half_window

    # Shift window if it extends beyond boundaries
    if start < 1:
        shift = 1 - start
        start = 1
        end = min(total_days, end + shift)
    elif end > total_days:
        shift = end - total_days
        end = total_days
        start = max(1, start - shift)

    return list(range(start, end + 1))


def load_all_routes(
    raw_path: Path,
    days: int,
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Load all GPX files and convert to Web Mercator coordinates."""
    routes = {}

    for day in range(1, days + 1):
        gpx_file = raw_path / f"day-{day:02d}.gpx"
        if gpx_file.exists():
            lats, lons = load_gpx_coordinates(gpx_file)
            if lats and lons:
                xs, ys = convert_to_web_mercator(lats, lons)
                routes[day] = (xs, ys)
        else:
            print(f"Warning: {gpx_file} not found")

    return routes


def generate_map_image(
    routes: dict[int, tuple[np.ndarray, np.ndarray]],
    current_day: int,
    window_days: list[int],
    output_path: Path,
) -> None:
    """Generate a map image for a specific day with context routes."""
    fig, ax = plt.subplots(
        figsize=(HORIZONTAL_PX / DPI, VERTICAL_PX / DPI),
        dpi=DPI,
    )

    # Collect all coordinates to determine map bounds
    all_xs = []
    all_ys = []

    # Plot context days first (so current day appears on top)
    for day in window_days:
        if day not in routes:
            continue

        xs, ys = routes[day]
        all_xs.extend(xs)
        all_ys.extend(ys)

        if day == current_day:
            continue  # Plot current day last

        ax.plot(
            xs,
            ys,
            color=CONTEXT_DAY_COLOR,
            linewidth=CONTEXT_DAY_WIDTH,
            alpha=CONTEXT_DAY_ALPHA,
            linestyle=CONTEXT_DAY_STYLE,
            label=f"Day {day}",
        )

    # Plot current day on top
    if current_day in routes:
        xs, ys = routes[current_day]
        ax.plot(
            xs,
            ys,
            color=CURRENT_DAY_COLOR,
            linewidth=CURRENT_DAY_WIDTH,
            alpha=1.0,
            label=f"Day {current_day} (current)",
        )

        # Add start/end markers for current day
        # ax.scatter(
        #    xs[0], ys[0], color="green", s=100, zorder=5, marker="o", label="Start"
        # )
        # ax.scatter(
        #    xs[-1], ys[-1], color="red", s=100, zorder=5, marker="s", label="End"
        # )

    # Set map bounds with padding, adjusted for 3:1 aspect ratio
    if all_xs and all_ys:
        x_min, x_max = min(all_xs), max(all_xs)
        y_min, y_max = min(all_ys), max(all_ys)

        x_range = x_max - x_min
        y_range = y_max - y_min

        # Add padding
        x_min -= x_range * MAP_PADDING
        x_max += x_range * MAP_PADDING
        y_min -= y_range * MAP_PADDING
        y_max += y_range * MAP_PADDING

        # Recalculate ranges with padding
        x_range = x_max - x_min
        y_range = y_max - y_min

        # Target aspect ratio (width:height)
        target_aspect = HORIZONTAL_PX / VERTICAL_PX

        # Current data aspect ratio
        data_aspect = x_range / y_range

        # Expand bounds to match target aspect while keeping map proportions
        if data_aspect > target_aspect:
            # Data is wider than target - expand y (height)
            new_y_range = x_range / target_aspect
            y_center = (y_min + y_max) / 2
            y_min = y_center - new_y_range / 2
            y_max = y_center + new_y_range / 2
        else:
            # Data is taller than target - expand x (width)
            new_x_range = y_range * target_aspect
            x_center = (x_min + x_max) / 2
            x_min = x_center - new_x_range / 2
            x_max = x_center + new_x_range / 2

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

    # Keep equal aspect so map isn't distorted
    ax.set_aspect("equal")

    # Add basemap tiles (use higher zoom for sharper tiles)
    cx.add_basemap(
        ax,
        source=cx.providers.CartoDB.Voyager,
        zoom=10,
        interpolation="spline36",
    )

    # Style the plot
    ax.set_axis_off()

    # Save the image
    plt.tight_layout()
    fig.savefig(output_path, format="jpeg", bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def main() -> None:
    """Generate map images for each day of the Camino."""
    # Ensure output directory exists
    OUT_PATH.mkdir(parents=True, exist_ok=True)

    # Load all routes once
    print("Loading GPX files...")
    routes = load_all_routes(RAW_PATH, DAYS)
    print(f"Loaded {len(routes)} routes")

    if not routes:
        print("No routes found. Check that GPX files exist in:", RAW_PATH)
        return

    # Generate image for each day
    for day in range(1, DAYS + 1):
        window_days = get_window_days(day, DAYS, WINDOW)
        output_file = OUT_PATH / f"camino-day-{day:02d}.jpg"

        print(
            f"Generating day {day:02d}: showing days {window_days} -> {output_file.name}"
        )

        generate_map_image(routes, day, window_days, output_file)

    print(f"\nDone! Generated {DAYS} images in {OUT_PATH}")


if __name__ == "__main__":
    main()

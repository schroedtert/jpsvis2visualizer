# Copyright © 2024 Tobias Schrödter
# SPDX-License-Identifier: MIT
"""Writes trajectories in JuPedSim sqlite format."""

import logging
import sqlite3
from pathlib import Path
from typing import Final

from pedpy import TrajectoryData, WalkableArea
from shapely import box, to_wkt

DATABASE_VERSION: Final = 2
_log = logging.getLogger(__name__)


def write_trajectory_to_sqlite(
    *,
    trajectory_data: TrajectoryData,
    walkable_area: WalkableArea = None,
    output_file: Path,
) -> None:
    """Writes the guven trajectory and geometry to output file.

    Args:
        trajectory_data (TrajectoryData): trajectory data
        walkable_area (WalkableArea): geometry in which the pedestrians/agents move
        output_file (Path): output fil
    """
    # TODO: support different modes (append, overwrite, do not overwrite)?

    connection = sqlite3.connect(output_file)

    if walkable_area is None:
        xmin, ymin, xmax, ymax = trajectory_data.bounds
        walkable_area = WalkableArea(box(xmin - 1, ymin - 1, xmax + 1, ymax + 1))
        _log.warning(
            f"No walkable area provided. Use bounding box instead: {walkable_area.polygon.wkt}"
        )

    _setup_sqlite_database(
        connection=connection, trajectory_data=trajectory_data, walkable_area=walkable_area
    )
    _write_sqlite_database(
        connection=connection, trajectory_data=trajectory_data, walkable_area=walkable_area
    )


def _setup_sqlite_database(
    *, connection: sqlite3.Connection, trajectory_data: TrajectoryData, walkable_area: WalkableArea
) -> None:
    fps = trajectory_data.frame_rate
    geometry = to_wkt(walkable_area.polygon, rounding_precision=-1)

    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute("DROP TABLE IF EXISTS trajectory_data")
        cursor.execute(
            "CREATE TABLE trajectory_data ("
            "   frame INTEGER NOT NULL,"
            "   id INTEGER NOT NULL,"
            "   pos_x REAL NOT NULL,"
            "   pos_y REAL NOT NULL,"
            "   ori_x REAL NOT NULL,"
            "   ori_y REAL NOT NULL)"
        )
        cursor.execute("DROP TABLE IF EXISTS metadata")
        cursor.execute(
            "CREATE TABLE metadata(key TEXT NOT NULL UNIQUE PRIMARY KEY, value TEXT NOT NULL)"
        )
        cursor.executemany(
            "INSERT INTO metadata VALUES(?, ?)",
            (("version", DATABASE_VERSION), ("fps", fps)),
        )
        cursor.execute("DROP TABLE IF EXISTS geometry")
        cursor.execute(
            "CREATE TABLE geometry(" "   hash INTEGER NOT NULL, " "   wkt TEXT NOT NULL)"
        )
        cursor.execute("CREATE UNIQUE INDEX geometry_hash on geometry( hash)")
        cursor.execute(
            "INSERT INTO geometry VALUES(?, ?)",
            (hash(geometry), geometry),
        )
        cursor.execute("DROP TABLE IF EXISTS frame_data")
        cursor.execute(
            "CREATE TABLE frame_data("
            "   frame INTEGER NOT NULL,"
            "   geometry_hash INTEGER NOT NULL)"
        )

        cursor.execute("CREATE INDEX frame_id_idx ON trajectory_data(frame, id)")
        cursor.execute("COMMIT")
    except sqlite3.Error as e:
        cursor.execute("ROLLBACK")
        raise RuntimeError(f"Error creating database: {e}") from e


def _write_sqlite_database(
    *,
    connection: sqlite3.Connection,
    trajectory_data: TrajectoryData,
    walkable_area: WalkableArea,
) -> None:
    cur = connection.cursor()
    data = trajectory_data.data
    min_frame, _ = trajectory_data.frame_range
    try:
        cur.execute("BEGIN")

        data["zero"] = 0  # dummy column for orientation
        data["frame"] -= min_frame  # the visualizer starts at frame zero
        traj_data = list(
            data[["frame", "id", "x", "y", "zero", "zero"]].itertuples(index=False, name=None)
        )
        cur.executemany(
            "INSERT INTO trajectory_data VALUES(?, ?, ?, ?, ?, ?)",
            traj_data,
        )

        geo_wkt = to_wkt(walkable_area.polygon, rounding_precision=-1)
        geo_hash = hash(geo_wkt)

        cur.execute(
            "INSERT OR IGNORE INTO geometry(hash, wkt) VALUES(?,?)",
            (geo_hash, geo_wkt),
        )

        frame_min, frame_max = trajectory_data.frame_range
        frames = list(range(frame_min, frame_max + 1))
        frame_geo_data = [(frame, geo_hash) for frame in frames]
        cur.executemany(
            "INSERT OR IGNORE INTO frame_data VALUES(?,?)",
            frame_geo_data,
        )

        xmin, ymin, xmax, ymax = walkable_area.bounds
        cur.executemany(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES(?,?)",
            [
                ("xmin", str(xmin)),
                ("xmax", str(xmax)),
                ("ymin", str(ymin)),
                ("ymax", str(ymax)),
            ],
        )

        cur.execute("COMMIT")
    except sqlite3.Error as e:
        cur.execute("ROLLBACK")
        raise RuntimeError(f"Error creating database: {e}") from e

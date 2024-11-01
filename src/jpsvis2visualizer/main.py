# Copyright © 2024 Tobias Schrödter
# SPDX-License-Identifier: MIT
"""CLI interface to convert txt trajectories to JuPedSim sqlite."""

import warnings
from pathlib import Path
from typing import Optional

import typer
from pedpy import TrajectoryData, WalkableArea, load_trajectory_from_txt
from tqdm import tqdm
from typing_extensions import Annotated
from writer import write_trajectory_to_sqlite


def _load_trajectory_data(trajectory_file: Path) -> TrajectoryData:
    return load_trajectory_from_txt(trajectory_file=trajectory_file)


def _validate_geometry_options(
    geometry: Optional[str], geometry_file: Optional[Path]
) -> Optional[WalkableArea]:
    """Ensure only one of geometry or geometry_file is provided.

    Raises a typer.BadParameter error if both are provided.
    """
    if geometry and geometry_file:
        raise typer.BadParameter("Cannot use both --geometry and --geometry_file at the same time.")

    if geometry:
        typer.echo(f"Using geometry: {geometry}")
        return WalkableArea(geometry)

    if geometry_file:
        typer.echo(f"Using geometry file: {geometry_file}")
        with open(geometry_file, "r") as file:
            wkt = file.readline().strip()  # Remove trailing newline or whitespace if needed
        return WalkableArea(wkt)

    typer.echo("Approximating geometry from file data.")
    return None


def _auto_generate_output(input_path: Path) -> Path:
    """Generate an output path by replacing the file extension of the input.

    Parameters:
    - input_path: The input file path as a Path object.

    Returns:
    - A Path object with the new file extension.
    """
    return input_path.with_suffix(".sqlite")


def convert_files(
    file_pattern: str,
    output_file: Optional[Path] = None,
    geometry: Optional[str] = None,
    geometry_file: Optional[Path] = None,
) -> None:
    """Convert a single file or multiple files matching a pattern to a new format."""
    walkable_area = _validate_geometry_options(geometry, geometry_file)
    files = list(Path().cwd().glob(file_pattern))

    if not files:
        typer.echo("No files found matching the pattern.")
        return

    total_files = len(files)

    with tqdm(total=total_files, desc="Processing files") as pbar:
        for file in files:
            output = output_file or _auto_generate_output(file)

            # Set the description to show the current file being processed
            pbar.set_description(f"Processing: {file.name} -> {output}")
            pbar.update(1)  # Increment the progress bar

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trajectory_data = _load_trajectory_data(file)
                write_trajectory_to_sqlite(trajectory_data, walkable_area, output_file=output)

    print("Finished converting files")


def main(
    file_pattern: str,
    output_file: Annotated[Optional[Path], typer.Option(help="Specify output file path.")] = None,
    geometry: Annotated[Optional[str], typer.Option(help="Geometry option.")] = None,
    geometry_file: Annotated[Optional[Path], typer.Option(help="Specify output file path.")] = None,
) -> None:
    """Convert given files to JuPedSim sqlite format.

    Args:
        file_pattern: _description_
        output_file: _description_.
        geometry: _description_.
        geometry_file: _description_.
    """
    convert_files(file_pattern, output_file, geometry, geometry_file)


if __name__ == "__main__":
    typer.run(main)

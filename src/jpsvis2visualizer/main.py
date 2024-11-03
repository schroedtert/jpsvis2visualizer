# Copyright © 2024 Tobias Schrödter
# SPDX-License-Identifier: MIT
"""CLI interface to convert txt trajectories to JuPedSim sqlite."""

import logging
import warnings
from pathlib import Path
from typing import Optional

import typer
from pedpy import TrajectoryData, WalkableArea, load_trajectory_from_txt
from tqdm import tqdm
from typing_extensions import Annotated

from jpsvis2visualizer.writer import write_trajectory_to_sqlite

app = typer.Typer()


def _load_trajectory_data(trajectory_file: Path, frame_rate: float | None) -> TrajectoryData:
    return load_trajectory_from_txt(trajectory_file=trajectory_file, default_frame_rate=frame_rate)


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


def _validate_output_file(number_files: int) -> None:
    if number_files > 1:
        raise typer.BadParameter(
            "Cannot use both --output-file if the file pattern matches multiple files"
        )


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
    frame_rate: Optional[float] = None,
) -> None:
    """Convert a single file or multiple files matching a pattern to a new format."""
    walkable_area = _validate_geometry_options(geometry, geometry_file)
    files = list(Path().cwd().glob(file_pattern))

    if not files:
        typer.echo("No files found matching the pattern.")
        return

    number_files = len(files)
    _validate_output_file(number_files=number_files)

    # Temporarily disable logging for write_trajectory_to_sqlite
    logging_level = logging.getLogger().getEffectiveLevel()  # Store current level
    logging.getLogger().setLevel(logging.ERROR)  # Suppress lower-level log messages

    with tqdm(total=number_files, desc="Processing files") as pbar:
        for file in files:
            output = output_file or _auto_generate_output(file)

            # Set the description to show the current file being processed
            pbar.set_description(f"Processing: {file.name} -> {output}")
            pbar.update(1)  # Increment the progress bar

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trajectory_data = _load_trajectory_data(file, frame_rate)
                write_trajectory_to_sqlite(
                    trajectory_data=trajectory_data, walkable_area=walkable_area, output_file=output
                )

    # Restore original logging level after function completes
    logging.getLogger().setLevel(logging_level)

    print("Finished converting files")


@app.command()
def main(
    file_pattern: Annotated[str, typer.Argument(help="Name pattern of files to convert.")],
    output_file: Annotated[
        Optional[Path], typer.Option("--output", "-o", help="Specify output file path.")
    ] = None,
    geometry: Annotated[
        Optional[str], typer.Option("--geometry", "-g", help="Geometry option.")
    ] = None,
    geometry_file: Annotated[
        Optional[Path], typer.Option("--geometry-file", "-gf", help="Specify output file path.")
    ] = None,
    frame_rate: Annotated[
        Optional[float],
        typer.Option(
            "--frame-rate",
            "-fps",
            help="Frame rate used in the files "
            "(otherwise will try to parse it from the input file).",
        ),
    ] = None,
) -> None:
    """Convert given files to JuPedSim sqlite format.

        ..................;oOXWMMMMWNKko;.......................................................................................................................................................................
    ................ckKWMMMMMMMMMMMWKkc.....................................................................................................................................................................
    ..............,kNMMMMMMMMMMMMMMMMWNk;...................................................................................................................................................................
    .............;OWMMMMMMMMMMMMMMMMMMWW0;..................................................................................................................................................................
    .............xWMMMMW0dxKWMMMMXkdkNMMWx..................................................................................................................................................................
    ............:KMMMMMO,..;OWMMKc...xWMM0;.................................................................................................................................................................
    .......;loolkNMMMMMKc..'kWMM0;..;OWMMXo:loo:'........,;...................................';'..............;cllc;...............;,..................................':,..;,.............................
    .....:ONMMMWWWWMMMMMNOolkKXX0ocdXWMMMWNWMMMW0c.......ld,..................................;dc............;ddollokk:............'oo'.................................c0l.,dl.............................
    ....lXMMMWXKNWWMMMMMMWd'.','..,kWMMMMNKOkKNMMNo......',...,',:::;......,:c:;'..,'......',..,'...;::::;...''.....;0x',,.......,'.,,...,:::;'...,'.....',....,:c:;'...lKl..,'..;;;;;;;,....,:::,.....,''::
    ...,kNX0x:'cKWWMMMMMMMXxl:;;:lkNMMMMMKc..':dkOo......dO;.c0Odoooxko'.;xxolldo;,xO;....,kx,:Ol.:xxoloodo,........o0l'oOl.....dO:,kx',dkollod:.;Od.....oO;..cdoooxOo..lKl.,Od.,ooood0Kd'.:xxdooxxc..;O0doo
    ....',,....oNMMMMMMMMMMMMWWNWMMMMMMMMK:..............d0;.lKd.....:0x,lKo'......;Ok,..'kO;.cKo.d0l'............:xx:..'x0:...o0l.,Ok'c0x,......;0x.....d0:.....'.'xK:.lKl.;0x.....,oko'.c0x;...,dKl.:Kk,..
    ..........,OWMMMMMMMMMMMMMMMMMMMMMMMMK:..............d0;.lKl......d0:'cdddddo;..:0x'.d0c..cKo.'lddddddo,....;dxc.....,kO;.l0o..,Ok'.cdddddd:.;0x.....d0:.,odollo0Kc.lKl.;0x....ckx;...xXkllooodkl.:0d...
    .........'xWWWMMMMMMMMMMMMMMMMMMMMMMMXc..............d0;.lKo.....:Ok,......:OO,..c0xx0l...cKo......''c0k'.,oxl'.......;OOd0x'..,Ok'......;k0;,0O,...'xK:.x0:...'xKc.lKl.;0x..;xkc.....c0x,........:0d...
    ........;kNMMMMMMMMMMMMMMMMMMMMMMMMWWNl..............d0;.lX0dolodko,.;dolcldkl....lKKo....:0l.:dolclldkc.:0Kxollll:'...:OXx'...'kx',odlcloko'.cOkolod00;.lOxlcclO0:.c0l.;Od.:OXkooooc'.:xxdlloo;..:Oo...
    ......;dXWMMMMMMMMMMMMMMMMMMMMMMMMMWWNo..............x0;.lKo;:cc;'....';ccc:'......,,......,'..':ccc:;'..'::::::::,.....';'.....,,..';ccc:'....':cc:,,,...':cc:;,;...,...,'.';::::::;....,:cc:,....,'...
    ...,lONMMMMMMWMMMMMMMMMMMMMWWMMMMMMMMWk'...........,l0k,.l0l............................................................................................................................................
    ,oOXWMMMWWWNNWMMMMMMMMMMMWWNNMMMMMMMMM0,...........;lc,..':'............................................................................................................................................
    KWMMMWNNXXNNWMMMMMMMMMMMWNXNWMMMMMMMMMX:................................................................................................................................................................
    xKXNNXXXNWMMMMMMMMMMMMMWNXXNMMMMMMMMMMK;................................................................................................................................................................
    ..,:lkXWMMMMMMMMMMMMMMNXXXXNMMMMMMMMNOc.................................................................................................................................................................
    .....'ckXWMMMMMMMWX0kdlc:cloxkkOOkxo:...................................................................................................................................................................
    ........:x0XWWNXOd:'....................................................................................................................................................................................
    """
    convert_files(
        file_pattern=file_pattern,
        output_file=output_file,
        geometry=geometry,
        geometry_file=geometry_file,
        frame_rate=frame_rate,
    )


if __name__ == "__main__":
    app()

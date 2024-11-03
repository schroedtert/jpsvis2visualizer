<div align="center">
    <img src="img/logo.png" height="100px">
</div>

-----------------

# jpsvis2visualizer

Converts txt trajectories to the latest sqlite format, which is readable with the visualizer.


## Install

```
pip install git+https://github.com/schroedtert/jpsvis2visualizer.git
```

## Usage as CLI application

```
jpsvis2visualizer [OPTIONS] FILE_PATTERN

```

### Required arguments:

| argument       | description                                                                                                                                                                                                                                                                                                                                              |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `FILE_PATTERN` | Name pattern of files to convert. Can use globbing patterns to convert multiple files at once. <br><br>  **Example:**<br> - `dir/traj.txt`: Convert the file `dir/traj.txt`<br> - `dir/*.txt`: Convert all files with `.txt` extension inside the folder `dir`.<br>  - `dir/**/*.txt`: Convert all files with `.txt` extension inside the folder `dir` and its subfolders.   |

### Options:

| option                   | description                                                                                                                   |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `--output`, `-o`         | Output file name. **Can only be used if `file_pattern` matches exactly one file.**                                            |
| `--geometry`, `-g`       | WKT of the geometry to write in the converted files.                                                                          |
| `--geometry-file`, `-gf` | File containing a single line, with the WKT of the geometry to write in the converted files.                                  |
| `--frame-rate`, `-fps`   | Frame rate used in the trajectory files. If none is given, it will be tried to determine the frame rate from the input files. |
|                          |                                                                                                                               |
> [!NOTE]  
> If no geometry information is provided. A bounding box around all trajectory points will be used. It will be extended by 1m to each side.

## Usage as library

Alternatively, if you want to convert files within your own scripts, you can import the `jpsvis2visualizer` module and call the write command directly. 
The trajectory needs to be converted to the [PedPy trajectory data format](https://pedpy.readthedocs.io/en/stable/api/data.html#trajectory_data.TrajectoryData).
If you want to save a specific geometry, it must be provided as [PedPy walkable area](https://pedpy.readthedocs.io/en/stable/api/data.html#geometry.WalkableArea).

```python
from jpsvis2visualizer import write_trajectory_to_sqlite

# create/load trajectory data
# create/load walkable area


# save the converted data to a file
write_trajectory_to_sqlite(trajectory_data=traj_data, output_file=out_file)
```

> [!NOTE]  
> If no geometry information is provided. A bounding box around all trajectory points will be used. It will be extended by 1m to each side.

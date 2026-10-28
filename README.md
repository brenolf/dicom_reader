# DICOM Reader

A lightweight desktop DICOM image viewer written in Python with Tkinter.

## Features

- Open an individual DICOM file or an entire folder
- Numeric filename ordering (`image1`, `image2`, `image10`)
- Left/right arrow navigation between files
- Multi-frame DICOM navigation
- Mouse-wheel zoom and click-and-drag panning
- Window/level reset and image inversion
- Optional metadata panel
- Support for common compressed DICOM formats
- 16-bit, float, and double-float pixel data handling
- Local virtual environment setup with no global Python dependencies

## Requirements

- Python 3.10 or newer
- Tkinter
- Internet access on first run to download Python packages

Tkinter is included with most Python installations. On some Linux distributions it must be installed separately through the operating system package manager.

## Run

```bash
./run.sh
```

Alternatively:

```bash
python3 run.py
```

The first run creates `.venv` inside the project and installs dependencies from `requirements.txt`. Later runs reuse the local environment.

## Usage

1. Click **Open File** to open one DICOM file, or **Open Folder** to load a series.
2. Use **Left** and **Right** arrow keys to move between files.
3. Scroll over the image to zoom.
4. Drag the image while zoomed in to pan.
5. Use **Show Info** to reveal metadata.
6. Use **Reset Window**, **Invert**, and **Reset Zoom** as needed.

## Supported pixel data

The viewer uses pydicom and pylibjpeg decoders for common JPEG, JPEG 2000, and RLE transfer syntaxes. It also handles standard, float, and double-float pixel data where supported by the DICOM file.

## Project layout

```text
 dicom_reader/
 ├── dicom_visualizer.py
 ├── requirements.txt
 ├── run.py
 └── run.sh
```

## License

No license has been specified yet.

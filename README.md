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

Python versions are not equally compatible with every optional decoder dependency:

- Python 3.10–3.14 installs `pylibjpeg-rle` for RLE-compressed DICOM files.
- Python 3.15 currently skips `pylibjpeg-rle` because its PyO3 build dependency does not yet support Python 3.15. Other listed dependencies can still be installed, but RLE-compressed files may not decode. Use Python 3.14 if you need the pylibjpeg RLE plugin.

Tkinter is included with most Python installations. On some Linux distributions it must be installed separately through the operating system package manager. On macOS, use a Python distribution that includes Tkinter; the OS-provided Python may have an older Tk version. After changing Python versions, remove the project's `.venv` and run the launcher again so it is recreated with the selected interpreter:

```bash
rm -rf .venv
./run.sh
```

## Run

```bash
./run.sh
```

Alternatively:

```bash
python3 run.py
```

The first run creates `.venv` inside the project and installs dependencies from `requirements.txt`. Later runs reuse the local environment. If you install or switch Python versions, remove `.venv` before launching so it is rebuilt with the new interpreter.

## Usage

1. Click **Open File** to open one DICOM file, or **Open Folder** to load a series.
2. Use **Left** and **Right** arrow keys to move between files.
3. Scroll over the image to zoom.
4. Drag the image while zoomed in to pan.
5. Use **Show Info** to reveal metadata.
6. Use **Reset Window**, **Invert**, and **Reset Zoom** as needed.

## Supported pixel data

The viewer uses pydicom and pylibjpeg decoders for common JPEG and JPEG 2000 transfer syntaxes. RLE decoding uses the optional `pylibjpeg-rle` plugin when available; that plugin is omitted on Python 3.15 until its build dependency supports that version, so RLE-compressed files may not decode there. The viewer also handles standard, float, and double-float pixel data where supported by the DICOM file.

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

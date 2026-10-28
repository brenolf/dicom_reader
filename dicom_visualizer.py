#!/usr/bin/env python3
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import pydicom
from PIL import Image, ImageTk
from pydicom.pixel_data_handlers.util import apply_modality_lut


class DicomVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Visualizer")
        self.geometry("1200x800")
        self.minsize(800, 600)

        self.dataset = None
        self.image_data = None
        self.display_image = None
        self.file_paths = []
        self.file_index = 0
        self.frame_index = 0
        self.window_center = None
        self.window_width = None
        self.invert = False
        self.zoom = 1.0

        self._build_ui()

    def _build_ui(self):
        self.colors = {
            "background": "#151517",
            "surface": "#202023",
            "surface_alt": "#2a2a2e",
            "border": "#38383d",
            "text": "#f5f5f7",
            "muted": "#a1a1a6",
            "accent": "#5e9eff",
            "canvas": "#0b0b0d",
        }
        self.configure(background=self.colors["background"])
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.colors["background"])
        style.configure("Surface.TFrame", background=self.colors["surface"])
        style.configure("Toolbar.TButton", background=self.colors["surface_alt"], foreground=self.colors["text"], borderwidth=0, padding=(12, 7))
        style.map("Toolbar.TButton", background=[("active", self.colors["accent"])])
        style.configure("Accent.TButton", background=self.colors["accent"], foreground="white", borderwidth=0, padding=(13, 7))
        style.map("Accent.TButton", background=[("active", "#82b4ff")])
        style.configure("App.TLabel", background=self.colors["background"], foreground=self.colors["text"])
        style.configure("Muted.TLabel", background=self.colors["background"], foreground=self.colors["muted"])
        style.configure("Surface.TLabel", background=self.colors["surface"], foreground=self.colors["text"])
        style.configure("Horizontal.TScale", background=self.colors["background"], troughcolor=self.colors["surface_alt"], borderwidth=0)

        header = ttk.Frame(self, style="App.TFrame", padding=(18, 16, 18, 12))
        header.pack(fill=tk.X)
        ttk.Label(header, text="DICOM Visualizer", style="App.TLabel", font=("TkDefaultFont", 16, "bold")).pack(side=tk.LEFT)
        self.file_label = ttk.Label(header, text="No file selected", style="Muted.TLabel")
        self.file_label.pack(side=tk.LEFT, padx=16)
        ttk.Button(header, text="Show Info", style="Toolbar.TButton", command=self.toggle_info).pack(side=tk.RIGHT)
        ttk.Button(header, text="Open Folder", style="Accent.TButton", command=self.open_folder).pack(side=tk.RIGHT, padx=(0, 8))
        ttk.Button(header, text="Open File", style="Toolbar.TButton", command=self.open_file).pack(side=tk.RIGHT, padx=(0, 8))

        main = ttk.Frame(self, style="App.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=18)
        self.image_frame = ttk.Frame(main, style="Surface.TFrame", padding=1)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.image_frame, background=self.colors["canvas"], highlightthickness=0, cursor="arrow")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _: self.render())
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.drag_pan)
        self.canvas.bind("<ButtonRelease-1>", self.end_pan)

        self.info_visible = False
        self.info_frame = ttk.Frame(main, style="Surface.TFrame", padding=16, width=280)
        self.info_frame.pack_propagate(False)
        ttk.Label(self.info_frame, text="Image Details", style="Surface.TLabel", font=("TkDefaultFont", 12, "bold")).pack(anchor=tk.W)
        self.metadata = tk.Text(self.info_frame, wrap=tk.WORD, state=tk.DISABLED, background=self.colors["surface"], foreground=self.colors["text"], insertbackground=self.colors["text"], relief=tk.FLAT, borderwidth=0, padx=0, pady=14)
        self.metadata.pack(fill=tk.BOTH, expand=True)

        footer = ttk.Frame(self, style="App.TFrame", padding=(18, 12, 18, 16))
        footer.pack(fill=tk.X)
        nav = ttk.Frame(footer, style="App.TFrame")
        nav.pack(fill=tk.X)
        ttk.Button(nav, text="‹", style="Toolbar.TButton", command=lambda: self.change_file(-1)).pack(side=tk.LEFT)
        ttk.Button(nav, text="›", style="Toolbar.TButton", command=lambda: self.change_file(1)).pack(side=tk.LEFT, padx=(5, 12))
        self.frame_label = ttk.Label(nav, text="Frame 0 / 0", style="Muted.TLabel")
        self.frame_label.pack(side=tk.LEFT)
        self.window_label = ttk.Label(nav, text="Window —", style="Muted.TLabel")
        self.window_label.pack(side=tk.RIGHT)
        self.zoom_label = ttk.Label(nav, text="100%", style="Muted.TLabel")
        self.zoom_label.pack(side=tk.RIGHT, padx=16)

        self.frame_scale = ttk.Scale(footer, from_=0, to=0, command=self.change_frame, style="Horizontal.TScale")
        self.frame_scale.pack(fill=tk.X, pady=(10, 0))
        self.pan_x = 0
        self.pan_y = 0
        self.drag_start = None
        self.bind_all("<Left>", lambda _: self.change_file(-1))
        self.bind_all("<Right>", lambda _: self.change_file(1))

    def on_mousewheel(self, event):
        direction = event.delta if event.delta else (1 if event.num == 4 else -1)
        self.zoom = min(max(self.zoom + (0.1 if direction > 0 else -0.1), 0.1), 5.0)
        self.render()
        return "break"

    def start_pan(self, event):
        if self.zoom > 1:
            self.drag_start = (event.x, event.y)
            self.canvas.configure(cursor="fleur")

    def drag_pan(self, event):
        if self.drag_start is None:
            return
        self.pan_x += event.x - self.drag_start[0]
        self.pan_y += event.y - self.drag_start[1]
        self.drag_start = (event.x, event.y)
        self.render()

    def end_pan(self, _):
        self.drag_start = None
        self.canvas.configure(cursor="arrow")

    def toggle_info(self):
        self.info_visible = not self.info_visible
        if self.info_visible:
            self.info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))
        else:
            self.info_frame.pack_forget()

    def reset_zoom(self):
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.render()

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open DICOM file",
            filetypes=[("DICOM files", "*.dcm *.dicom"), ("All files", "*")],
        )
        if not path:
            return
        self.file_paths = [path]
        self.file_index = 0
        self.load_file(path)

    def open_folder(self):
        folder = filedialog.askdirectory(title="Open DICOM folder")
        if not folder:
            return
        paths = []
        names = sorted(
            os.listdir(folder),
            key=lambda name: (
                int(re.sub(r"\D", "", name))
                if re.search(r"\d", name)
                else float("inf"),
                name.lower(),
            ),
        )
        for name in names:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                try:
                    dataset = pydicom.dcmread(path, defer_size=1)
                    if self.has_pixel_data(dataset):
                        paths.append(path)
                except Exception:
                    continue
        if not paths:
            messagebox.showerror("No DICOM files", "No readable DICOM files were found in that folder.")
            return
        self.file_paths = paths
        self.file_index = 0
        self.load_file(paths[0])

    @staticmethod
    def has_pixel_data(dataset):
        return any(
            tag in dataset
            for tag in ((0x7FE0, 0x0010), (0x7FE0, 0x0008), (0x7FE0, 0x0009))
        )

    def decode_pixels(self, dataset):
        if (0x7FE0, 0x0010) in dataset:
            return dataset.pixel_array
        rows = int(dataset.Rows)
        columns = int(dataset.Columns)
        frames = int(getattr(dataset, "NumberOfFrames", 1))
        samples = int(getattr(dataset, "SamplesPerPixel", 1))
        tag = (0x7FE0, 0x0008) if (0x7FE0, 0x0008) in dataset else (0x7FE0, 0x0009)
        dtype = np.dtype("f4" if tag[1] == 0x0008 else "f8")
        if not dataset.is_little_endian:
            dtype = dtype.newbyteorder(">")
        pixels = np.frombuffer(dataset[tag].value, dtype=dtype)
        shape = (rows, columns) if samples == 1 else (rows, columns, samples)
        if frames > 1:
            shape = (frames,) + shape
        return pixels.reshape(shape)

    def load_file(self, path):
        try:
            dataset = pydicom.dcmread(path)
            if not self.has_pixel_data(dataset):
                raise ValueError("This DICOM file contains no image pixel data.")
            pixels = apply_modality_lut(self.decode_pixels(dataset), dataset)
            self.dataset = dataset
            self.image_data = np.asarray(pixels)
            self.frame_index = 0
            self.invert = False
            self.zoom = 1.0
            self.pan_x = 0
            self.pan_y = 0
            self.frame_scale.configure(to=max(self.frame_count - 1, 0), value=0)
            self.reset_window()
            self.file_label.configure(
                text=f"{os.path.basename(path)} ({self.file_index + 1} / {len(self.file_paths)})"
            )
            self.show_metadata(path)
        except Exception as error:
            messagebox.showerror("Unable to open DICOM", str(error))

    def change_file(self, direction):
        if len(self.file_paths) <= 1:
            return
        new_index = self.file_index + direction
        if 0 <= new_index < len(self.file_paths):
            self.file_index = new_index
            self.load_file(self.file_paths[self.file_index])

    @property
    def frame_count(self):
        if self.image_data is None:
            return 0
        if self.image_data.ndim == 2:
            return 1
        samples = int(getattr(self.dataset, "SamplesPerPixel", 1))
        if self.image_data.ndim == 3 and samples > 1 and self.image_data.shape[-1] == samples:
            return 1
        return self.image_data.shape[0]

    def current_frame(self):
        if self.frame_count > 1:
            return self.image_data[self.frame_index]
        return self.image_data

    def reset_window(self):
        if self.image_data is None:
            return
        frame = self.current_frame().astype(np.float32)
        if frame.ndim == 3:
            self.window_center = float(np.mean(frame))
            self.window_width = max(float(np.ptp(frame)), 1.0)
        else:
            low, high = np.percentile(frame, [1, 99])
            self.window_center = float((low + high) / 2)
            self.window_width = max(float(high - low), 1.0)
        self.render()

    def toggle_invert(self):
        self.invert = not self.invert
        self.render()

    def change_frame(self, value):
        if self.frame_count <= 1:
            return
        self.frame_index = min(int(float(value)), self.frame_count - 1)
        self.update_position_label()
        self.render()

    def render(self):
        if self.image_data is None or self.canvas.winfo_width() <= 1:
            return
        frame = self.current_frame().astype(np.float32)
        photometric = str(getattr(self.dataset, "PhotometricInterpretation", ""))
        if frame.ndim == 3 and frame.shape[-1] in (3, 4) and photometric not in ("MONOCHROME1", "MONOCHROME2"):
            image = self.to_rgb(frame)
        else:
            image = self.to_grayscale(frame)
        available_width = max(self.canvas.winfo_width(), 1)
        available_height = max(self.canvas.winfo_height(), 1)
        fit_scale = min(available_width / image.width, available_height / image.height)
        scale = max(fit_scale * self.zoom, 0.01)
        size = (max(int(image.width * scale), 1), max(int(image.height * scale), 1))
        image = image.resize(size, Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(
            self.canvas.winfo_width() // 2 + self.pan_x,
            self.canvas.winfo_height() // 2 + self.pan_y,
            image=self.display_image,
        )
        self.window_label.configure(text=f"Window {self.window_center:.1f} / {self.window_width:.1f}")
        self.update_position_label()
        self.zoom_label.configure(text=f"{int(self.zoom * 100)}%")

    def update_position_label(self):
        file_position = f"File {self.file_index + 1} / {len(self.file_paths)}"
        frame_position = f"Frame {self.frame_index + 1} / {self.frame_count}"
        self.frame_label.configure(text=f"{file_position}  ·  {frame_position}")

    def to_grayscale(self, frame):
        low = self.window_center - self.window_width / 2
        high = self.window_center + self.window_width / 2
        normalized = np.clip((frame - low) / max(high - low, 1), 0, 1)
        if self.invert:
            normalized = 1 - normalized
        values = (normalized * 255).astype(np.uint8)
        return Image.fromarray(values, mode="L")

    def to_rgb(self, frame):
        values = np.asarray(frame[..., :3], dtype=np.float32)
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
        low = np.min(values, axis=(0, 1), keepdims=True)
        high = np.max(values, axis=(0, 1), keepdims=True)
        normalized = np.clip((values - low) / np.maximum(high - low, 1), 0, 1)
        if self.invert:
            normalized = 1 - normalized
        return Image.fromarray((normalized * 255).astype(np.uint8), mode="RGB")

    def show_metadata(self, path):
        fields = [
            ("File", path),
            ("Patient", getattr(self.dataset, "PatientName", "Unknown")),
            ("Study", getattr(self.dataset, "StudyDescription", "Unknown")),
            ("Series", getattr(self.dataset, "SeriesDescription", "Unknown")),
            ("Modality", getattr(self.dataset, "Modality", "Unknown")),
            ("Rows", getattr(self.dataset, "Rows", "Unknown")),
            ("Columns", getattr(self.dataset, "Columns", "Unknown")),
            ("Photometric", getattr(self.dataset, "PhotometricInterpretation", "Unknown")),
            ("Frames", self.frame_count),
        ]
        self.metadata.configure(state=tk.NORMAL)
        self.metadata.delete("1.0", tk.END)
        for label, value in fields:
            self.metadata.insert(tk.END, f"{label}:\n{value}\n\n")
        self.metadata.configure(state=tk.DISABLED)


if __name__ == "__main__":
    DicomVisualizer().mainloop()

# 🎥 LiveObjectDetection

<div align="center">

### **High-Performance Real-Time Camera Object Detection, Tracking & AI Annotation Suite**

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-aff.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/platform-windows%20x64-0078d7.svg)](https://github.com/VicRoger27/LiveObjectDetection)
[![Hardware: DirectML | CUDA | CPU](https://img.shields.io/badge/hardware-DirectML%20%7C%20CUDA%20%7C%20CPU-10b981.svg)](https://github.com/VicRoger27/LiveObjectDetection)

[**Features**](#-key-features) •
[**Quick Start**](#-quick-start) •
[**Live Camera Controls**](#-live-camera-pipeline--shortcuts) •
[**Hardware Acceleration**](#-hardware-acceleration) •
[**Model Zoo**](#-model-zoo) •
[**Offline Help**](#-offline-documentation)

</div>

---

## 🌟 Overview

**LiveObjectDetection** combines the real-time camera detection workflow and HUD overlay inspired by [TorchObjectDetection](https://github.com/hasnocool/TorchObjectDetection) with the comprehensive deep learning model zoo, dataset annotation studio, and hardware acceleration from [X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling).

Unlike traditional labeling tools that only work with static image files, **LiveObjectDetection** connects directly to your webcams, capture cards, and RTSP network streams to deliver real-time AI object detection, live telemetry diagnostics, and a seamless **Freeze-to-Label (Spacebar)** workflow for instant dataset creation.

---

## 🚀 Key Features

- 🖥️ **Zero-Python Desktop Experience**:
  Run directly via the pre-built multi-file application (`LiveAnyLabeling.exe`) or install system-wide with the installer (`LiveAnyLabeling_Setup.exe`) — no Python environment required.

- 📹 **Real-Time Live Camera Inference**:
  Connect to USB webcams, virtual cameras, or RTSP/HTTP network video streams. Runs high-efficiency multi-threaded inference at 30–60+ FPS.

- 🎛️ **3 Dynamic Viewing Modes**:
  1. **Integrated Canvas Mode**: Detections are rendered smoothly onto the primary interactive annotation workspace.
  2. **Continuous Monitor HUD Mode**: A transparent diagnostic telemetry HUD displays real-time Camera FPS, Inference Latency (ms), Video Resolution, and Detected Object Count.
  3. **Dual-Pane Mode**: Side-by-side split screen comparing raw camera capture with the AI-detected output.

- 📸 **Spacebar Freeze-to-Label**:
  Hit `Spacebar` or click **Freeze / Snapshot to Label** while the camera is streaming to instantly pause the current frame and convert all live detections into editable bounding boxes or polygons on the canvas.

- ⚡ **Resolution Presets**:
  Supports Native, 720p HD, 1080p FHD (1920x1080), 2K QHD (2560x1440), and 4K UHD (3840x2160) streaming with decoupled capture and inference pipelines.

- 🛠️ **1-Click Hardware Acceleration Manager**:
  A built-in Voicebox-style runtime selector (`Camera` > `Hardware Acceleration Manager...`) that allows 1-click downloads and switching between **CPU**, **DirectML** (works on AMD Radeon, Intel Arc, and NVIDIA GPUs), and **CUDA** acceleration.

- 🧠 **Pre-Loaded Model Zoo**:
  Comes bundled with ready-to-run YOLO models in the `models/` directory:
  - `yolov8n.pt` (Ultra-fast, preloaded by default)
  - `yolov10s.pt`, `yolov10m.pt`, `yolov10b.pt`
  - `yolov9c.pt`
  - Seamless support for YOLO11, RT-DETR, Segment Anything (SAM 2), MobileSAM, GroundingDINO, YOLO-World, and custom ONNX/PyTorch models.

- 📁 **Universal Dataset Import & Export**:
  Export annotated datasets directly to **YOLO**, **COCO**, **VOC Pascal**, **LabelMe**, **DOTA**, **MOT**, and **XLABEL** formats.

---

## 📦 Quick Start

### Option 1: Run Pre-Built Windows Executable (No Python Required)

1. Clone or download this repository.
2. Launch `LiveAnyLabeling.exe` directly from the root directory, or run `LiveAnyLabeling_Setup.exe` to install it into your Windows Start Menu and Desktop.
3. The **Live Camera & Object Detection** panel is immediately open on the right:
   - Select your camera device (Camera 0 is selected by default).
   - Select your detection model (e.g. `Local: yolov8n.pt`).
   - Click the green **▶ Start Live Camera** button or press `Ctrl+Shift+C`.

### Option 2: Run from Source

```powershell
# Clone the repository
git clone https://github.com/VicRoger27/LiveObjectDetection.git
cd LiveObjectDetection

# Create and activate a Python virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch LiveObjectDetection
python -m anylabeling.app
```

---

## ⌨️ Live Camera Pipeline & Shortcuts

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Ctrl+Shift+C` | **Toggle Live Camera** | Opens / closes the camera control dock and stream |
| `Spacebar` | **Freeze Snapshot** | Freezes live video frame and loads detections onto canvas |
| `Ctrl+O` | **Open Image/Label** | Open static image or existing annotation |
| `Ctrl+U` | **Open Video** | Open local video file for sequential labeling |
| `Ctrl+S` | **Save Annotation** | Save current annotation to disk |
| `F1` | **Camera Guide** | Opens the built-in offline Live Camera HTML user guide |

---

## ⚡ Hardware Acceleration

Navigate to **Camera** > **Hardware Acceleration Manager...** in the top menu to view and configure your active inference runtime:

- **CPU Mode**: Safe universal fallback, compatible with any x86_64 processor.
- **DirectML Mode**: High-performance DirectX 12 hardware acceleration across **AMD Radeon**, **Intel Arc / Iris Xe**, and **NVIDIA GeForce** graphics cards.
- **CUDA Mode**: Dedicated NVIDIA Tensor Core GPU acceleration for maximum throughput.

---

## 🧠 Model Zoo

The application detects local `.pt` and `.onnx` models stored in the root `models/` directory automatically. You can switch models on the fly from the camera control dock without restarting the stream:

- `models/yolov8n.pt` — Nano detector for extreme framerates (60+ FPS).
- `models/yolov10s.pt` / `yolov10m.pt` / `yolov10b.pt` — State-of-the-art NMS-free YOLOv10 detectors.
- `models/yolov9c.pt` — High-accuracy YOLOv9 model.
- **Custom Models**: Drop any custom PyTorch (`.pt`) or ONNX (`.onnx`) model into the `models/` directory, and it will appear in the **Detection Model** dropdown.

---

## 📖 Offline Documentation

The app includes standalone, rich HTML guides accessible directly from the **Help** menu:
- `help_camera.html`: Live Camera Quickstart, resolution tuning, RTSP setup, and freeze-to-label guide.
- `help_en.html`: Complete user manual for annotation shapes, auto-labeling, and dataset conversion.

---

## 🤝 Acknowledgements

- [TorchObjectDetection](https://github.com/hasnocool/TorchObjectDetection) — Concept and foundation for real-time live PyTorch camera detection.
- [X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) — Core annotation engine and multi-modal architecture.
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) — Deep learning object detection models.

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0](./LICENSE).

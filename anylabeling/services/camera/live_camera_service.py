import os
import time
import threading
from typing import Optional, Tuple, List, Union

import cv2
import numpy as np
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QObject, pyqtSignal

from anylabeling.views.labeling.shape import Shape
from anylabeling.views.labeling.logger import logger


RESOLUTION_PRESETS = {
    "4K UHD (3840x2160)": (3840, 2160),
    "2K QHD (2560x1440)": (2560, 1440),
    "1080p FHD (1920x1080)": (1920, 1080),
    "720p HD (1280x720)": (1280, 720),
    "Device Native Max": (0, 0),
}


class LiveCameraService(QObject):
    """
    High-performance multi-threaded camera capture and live AI inference service.
    Decouples video capture from AI inference to guarantee smooth, low-latency display.
    """

    frame_ready = pyqtSignal(QtGui.QImage, list, dict)  # qimage, shapes, stats
    raw_frame_ready = pyqtSignal(np.ndarray, list)  # raw_bgr, shapes
    camera_started = pyqtSignal(int, int)  # width, height
    camera_stopped = pyqtSignal()
    camera_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap: Optional[cv2.VideoCapture] = None
        self.device_id: Union[int, str] = 0
        self.requested_resolution: Tuple[int, int] = (1920, 1080)
        self.actual_width: int = 0
        self.actual_height: int = 0

        self.is_running: bool = False
        self.is_paused: bool = False
        self.inference_enabled: bool = True

        self.model = None
        self.conf_threshold: float = 0.45
        self.iou_threshold: float = 0.45
        self.class_filters: Optional[List[str]] = None

        self._lock = threading.Lock()
        self._latest_raw_frame: Optional[np.ndarray] = None
        self._latest_shapes: List[Shape] = []
        self._latest_stats: dict = {}

        self._capture_thread: Optional[threading.Thread] = None
        self._inference_thread: Optional[threading.Thread] = None

        # Stats tracking
        self._fps_count: int = 0
        self._fps_start_time: float = time.time()
        self._current_fps: float = 0.0
        self._infer_fps: float = 0.0
        self._infer_latency_ms: float = 0.0

        # Auto-save support
        self.auto_save_enabled: bool = False
        self.auto_save_interval: float = 2.0  # seconds
        self.auto_save_dir: str = ""
        self._last_auto_save_time: float = 0.0

    @staticmethod
    def scan_available_cameras(max_tested: int = 6) -> List[int]:
        """Scan system for available video capture devices."""
        available = []
        for i in range(max_tested):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available if available else [0]

    def set_model(self, model):
        """Set the active auto-labeling model."""
        with self._lock:
            self.model = model

    def set_thresholds(self, conf: float, iou: float):
        """Update detection thresholds."""
        with self._lock:
            self.conf_threshold = conf
            self.iou_threshold = iou

    def set_class_filters(self, classes: Optional[List[str]]):
        """Set allowed classes for detection."""
        with self._lock:
            self.class_filters = classes

    def set_resolution(self, width: int, height: int):
        """Request a specific resolution preset."""
        self.requested_resolution = (width, height)
        if self.cap and self.cap.isOpened():
            self._apply_resolution(self.cap, width, height)

    def _apply_resolution(self, cap: cv2.VideoCapture, width: int, height: int) -> Tuple[int, int]:
        if width > 0 and height > 0:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        else:
            # Native max attempt: try high res fallback
            for w, h in [(3840, 2160), (2560, 1440), (1920, 1080), (1280, 720)]:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if actual_w == w and actual_h == h:
                    break

        self.actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(f"Live camera negotiated resolution: {self.actual_width}x{self.actual_height}")
        return self.actual_width, self.actual_height

    def start_camera(self, device_id: Union[int, str] = 0, resolution: Optional[Tuple[int, int]] = None):
        """Start camera capture and inference worker threads."""
        if self.is_running:
            self.stop_camera()

        self.device_id = device_id
        if resolution:
            self.requested_resolution = resolution

        try:
            backend = cv2.CAP_DSHOW if (isinstance(device_id, int) and os.name == 'nt') else cv2.CAP_ANY
            self.cap = cv2.VideoCapture(device_id, backend)
            if not self.cap.isOpened():
                # Fallback without DSHOW
                self.cap = cv2.VideoCapture(device_id)

            if not self.cap.isOpened():
                raise RuntimeError(f"Cannot open camera device {device_id}")

            self._apply_resolution(self.cap, self.requested_resolution[0], self.requested_resolution[1])
            self.is_running = True
            self.is_paused = False

            # Start worker threads
            self._capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
            self._capture_thread.start()

            self._inference_thread = threading.Thread(target=self._inference_worker, daemon=True)
            self._inference_thread.start()

            self.camera_started.emit(self.actual_width, self.actual_height)
        except Exception as e:
            self.is_running = False
            logger.error(f"Failed to start camera: {e}")
            self.camera_error.emit(str(e))

    def stop_camera(self):
        """Stop camera capture and release device."""
        self.is_running = False
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=1.0)
        if self._inference_thread and self._inference_thread.is_alive():
            self._inference_thread.join(timeout=1.0)

        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                logger.warning(f"Error releasing camera: {e}")
            self.cap = None

        self.camera_stopped.emit()

    def toggle_pause(self) -> bool:
        """Pause or resume live stream."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def get_snapshot(self) -> Tuple[Optional[QtGui.QImage], Optional[np.ndarray], List[Shape]]:
        """Get instantaneous copy of current frame and its detected shapes."""
        with self._lock:
            if self._latest_raw_frame is None:
                return None, None, []
            raw_copy = self._latest_raw_frame.copy()
            shapes_copy = [shape.copy() for shape in self._latest_shapes]

        # Convert to QImage
        h, w, ch = raw_copy.shape
        rgb_frame = cv2.cvtColor(raw_copy, cv2.COLOR_BGR2RGB)
        bytes_per_line = ch * w
        qimage = QtGui.QImage(
            rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888
        ).copy()
        return qimage, raw_copy, shapes_copy

    def _capture_worker(self):
        """Thread dedicated strictly to reading frames from camera hardware."""
        while self.is_running:
            if self.is_paused or self.cap is None:
                time.sleep(0.03)
                continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            with self._lock:
                self._latest_raw_frame = frame

            # Calculate camera FPS
            self._fps_count += 1
            elapsed = time.time() - self._fps_start_time
            if elapsed >= 1.0:
                self._current_fps = round(self._fps_count / elapsed, 1)
                self._fps_count = 0
                self._fps_start_time = time.time()

            # If no inference is enabled, emit directly for maximum smoothness
            if not self.inference_enabled or self.model is None:
                self._emit_frame(frame, [])

            time.sleep(0.005)

    def _inference_worker(self):
        """Thread dedicated to running AI model predictions on latest frames."""
        last_processed_frame = None
        infer_count = 0
        infer_start_time = time.time()

        while self.is_running:
            if self.is_paused or not self.inference_enabled or self.model is None:
                time.sleep(0.03)
                continue

            with self._lock:
                frame = self._latest_raw_frame

            if frame is None or frame is last_processed_frame:
                time.sleep(0.005)
                continue

            last_processed_frame = frame
            t0 = time.time()

            # Run detection
            shapes = self._run_detection_on_frame(frame)
            latency = (time.time() - t0) * 1000.0

            with self._lock:
                self._latest_shapes = shapes
                self._infer_latency_ms = round(latency, 1)

            infer_count += 1
            elapsed = time.time() - infer_start_time
            if elapsed >= 1.0:
                self._infer_fps = round(infer_count / elapsed, 1)
                infer_count = 0
                infer_start_time = time.time()

            # Emit frame with shapes
            self._emit_frame(frame, shapes)

            # Handle Auto-Save if enabled
            self._handle_auto_save(frame, shapes)

    def _run_detection_on_frame(self, frame: np.ndarray) -> List[Shape]:
        """Run the active model or Ultralytics model on the frame."""
        shapes: List[Shape] = []
        if self.model is None:
            return shapes

        try:
            h, w, _ = frame.shape
            # Case 1: X-AnyLabeling Model instance (has predict_shapes)
            if hasattr(self.model, "predict_shapes"):
                # Convert BGR frame to QImage for X-AnyLabeling models
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytes_per_line = 3 * w
                qimg = QtGui.QImage(
                    rgb_frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888
                )
                res = self.model.predict_shapes(qimg)
                if hasattr(res, "shapes") and res.shapes:
                    for s in res.shapes:
                        # Filter by confidence
                        if hasattr(s, "score") and s.score is not None:
                            if s.score < self.conf_threshold:
                                continue
                        # Filter by class if specified
                        if self.class_filters and s.label not in self.class_filters:
                            continue
                        shapes.append(s)

            # Case 2: Ultralytics YOLO model directly
            elif hasattr(self.model, "__call__"):
                results = self.model(frame, verbose=False, conf=self.conf_threshold, iou=self.iou_threshold)
                if results and len(results) > 0 and hasattr(results[0], "boxes"):
                    boxes = results[0].boxes
                    names = getattr(self.model, "names", {})
                    for box in boxes:
                        xyxy = box.xyxy[0].cpu().numpy().astype(float)
                        conf = float(box.conf[0].cpu().numpy())
                        cls_idx = int(box.cls[0].cpu().numpy())
                        label = names.get(cls_idx, str(cls_idx))

                        if self.class_filters and label not in self.class_filters:
                            continue

                        # Create X-AnyLabeling Shape (Rectangle)
                        shape = Shape(
                            label=label,
                            shape_type="rectangle",
                            score=conf,
                        )
                        shape.add_point(QtCore.QPointF(xyxy[0], xyxy[1]))
                        shape.add_point(QtCore.QPointF(xyxy[2], xyxy[3]))
                        shape.close()
                        shapes.append(shape)

        except Exception as e:
            logger.debug(f"Live detection frame error: {e}")

        return shapes

    def _emit_frame(self, frame: np.ndarray, shapes: List[Shape]):
        """Convert frame to QImage and emit Qt signal."""
        h, w, ch = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        bytes_per_line = ch * w
        qimage = QtGui.QImage(rgb.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888).copy()

        stats = {
            "fps": self._current_fps,
            "infer_fps": self._infer_fps,
            "latency_ms": self._infer_latency_ms,
            "width": w,
            "height": h,
            "count": len(shapes),
        }
        with self._lock:
            self._latest_stats = stats

        self.frame_ready.emit(qimage, shapes, stats)
        self.raw_frame_ready.emit(frame, shapes)

    def _handle_auto_save(self, frame: np.ndarray, shapes: List[Shape]):
        """Save frame and annotations if auto-save interval expired."""
        if not self.auto_save_enabled or not self.auto_save_dir:
            return

        now = time.time()
        if now - self._last_auto_save_time >= self.auto_save_interval:
            self._last_auto_save_time = now
            try:
                os.makedirs(self.auto_save_dir, exist_ok=True)
                timestamp = int(now * 1000)
                img_path = os.path.join(self.auto_save_dir, f"frame_{timestamp}.jpg")
                cv2.imwrite(img_path, frame)

                # Save annotations in JSON format
                json_path = os.path.join(self.auto_save_dir, f"frame_{timestamp}.json")
                import json
                shapes_data = []
                for s in shapes:
                    points = [[p.x(), p.y()] for p in getattr(s, "points", [])]
                    shapes_data.append({
                        "label": s.label,
                        "score": getattr(s, "score", 1.0),
                        "points": points,
                        "shape_type": getattr(s, "shape_type", "rectangle"),
                    })
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "version": "1.0",
                        "imagePath": os.path.basename(img_path),
                        "imageHeight": frame.shape[0],
                        "imageWidth": frame.shape[1],
                        "shapes": shapes_data,
                    }, f, indent=2)
                logger.info(f"Auto-saved live frame and annotations: {img_path}")
            except Exception as e:
                logger.error(f"Error in auto-save: {e}")

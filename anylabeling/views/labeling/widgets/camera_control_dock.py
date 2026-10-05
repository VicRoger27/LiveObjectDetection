import os
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal

from anylabeling.services.camera.live_camera_service import LiveCameraService, RESOLUTION_PRESETS


class CameraControlDock(QtWidgets.QDockWidget):
    """
    Comprehensive Live Camera Control & Telemetry Dock Widget.
    Features 3 viewing modes, resolution presets up to 4K, stream controls,
    freeze-to-label, auto-saving, and real-time telemetry.
    """

    view_mode_changed = pyqtSignal(str)  # "integrated", "monitor", "dual_pane"
    freeze_snapshot_requested = pyqtSignal()
    model_quick_switched = pyqtSignal(str)  # model path or name

    def __init__(self, camera_service: LiveCameraService, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Live Camera & Object Detection"))
        self.camera_service = camera_service
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(main_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ----------------- Section 1: Viewing Mode -----------------
        mode_group = QtWidgets.QGroupBox(self.tr("1. Viewing Mode"))
        mode_layout = QtWidgets.QVBoxLayout(mode_group)
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItem(self.tr("Integrated Canvas Mode"), "integrated")
        self.mode_combo.addItem(self.tr("Continuous Monitor HUD"), "monitor")
        self.mode_combo.addItem(self.tr("Dual-Pane (Side-by-Side)"), "dual_pane")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        layout.addWidget(mode_group)

        # ----------------- Section 2: Hardware Device & Resolution -----------------
        device_group = QtWidgets.QGroupBox(self.tr("2. Camera Device & Resolution"))
        dev_layout = QtWidgets.QGridLayout(device_group)

        # Device selector
        dev_layout.addWidget(QtWidgets.QLabel(self.tr("Device:")), 0, 0)
        self.device_combo = QtWidgets.QComboBox()
        self._refresh_cameras()
        dev_layout.addWidget(self.device_combo, 0, 1)

        self.btn_refresh = QtWidgets.QPushButton(self.tr("Scan"))
        self.btn_refresh.setToolTip(self.tr("Rescan available cameras"))
        self.btn_refresh.clicked.connect(self._refresh_cameras)
        dev_layout.addWidget(self.btn_refresh, 0, 2)

        # Custom Stream URL input
        dev_layout.addWidget(QtWidgets.QLabel(self.tr("Stream URL:")), 1, 0)
        self.stream_url_input = QtWidgets.QLineEdit()
        self.stream_url_input.setPlaceholderText(self.tr("Optional rtsp:// or http://"))
        dev_layout.addWidget(self.stream_url_input, 1, 1, 1, 2)

        # High-Fidelity Resolution Selector
        dev_layout.addWidget(QtWidgets.QLabel(self.tr("Resolution:")), 2, 0)
        self.res_combo = QtWidgets.QComboBox()
        for name in RESOLUTION_PRESETS:
            self.res_combo.addItem(name)
        # Default to 1080p FHD
        idx = self.res_combo.findText("1080p FHD (1920x1080)")
        if idx >= 0:
            self.res_combo.setCurrentIndex(idx)
        self.res_combo.currentIndexChanged.connect(self._on_resolution_changed)
        dev_layout.addWidget(self.res_combo, 2, 1, 1, 2)

        layout.addWidget(device_group)

        # ----------------- Section 3: Model & Detection Controls -----------------
        model_group = QtWidgets.QGroupBox(self.tr("3. Detection Model"))
        model_layout = QtWidgets.QVBoxLayout(model_group)

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItem(self.tr("[Active X-AnyLabeling Model]"), "active_anylabeling")
        # Add local models if found
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models"))
        if os.path.isdir(models_dir):
            for f in sorted(os.listdir(models_dir)):
                if f.endswith((".pt", ".onnx")):
                    self.model_combo.addItem(f"Local: {f}", os.path.join(models_dir, f))
        self.model_combo.currentIndexChanged.connect(self._on_model_selected)
        model_layout.addWidget(self.model_combo)

        # Thresholds
        thresh_layout = QtWidgets.QHBoxLayout()
        thresh_layout.addWidget(QtWidgets.QLabel(self.tr("Conf:")))
        self.conf_spin = QtWidgets.QDoubleSpinBox()
        self.conf_spin.setRange(0.05, 1.0)
        self.conf_spin.setSingleStep(0.05)
        self.conf_spin.setValue(0.45)
        self.conf_spin.valueChanged.connect(self._on_thresholds_changed)
        thresh_layout.addWidget(self.conf_spin)

        thresh_layout.addWidget(QtWidgets.QLabel(self.tr("IoU:")))
        self.iou_spin = QtWidgets.QDoubleSpinBox()
        self.iou_spin.setRange(0.05, 1.0)
        self.iou_spin.setSingleStep(0.05)
        self.iou_spin.setValue(0.45)
        self.iou_spin.valueChanged.connect(self._on_thresholds_changed)
        thresh_layout.addWidget(self.iou_spin)
        model_layout.addLayout(thresh_layout)

        layout.addWidget(model_group)

        # ----------------- Section 4: Live Stream Operations -----------------
        ctrl_group = QtWidgets.QGroupBox(self.tr("4. Stream Operations"))
        ctrl_layout = QtWidgets.QVBoxLayout(ctrl_group)

        btn_row1 = QtWidgets.QHBoxLayout()
        self.btn_toggle_camera = QtWidgets.QPushButton(self.tr("Start Camera"))
        self.btn_toggle_camera.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #388e3c; }"
        )
        self.btn_toggle_camera.clicked.connect(self._toggle_camera)
        btn_row1.addWidget(self.btn_toggle_camera)

        self.btn_pause = QtWidgets.QPushButton(self.tr("Pause"))
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._toggle_pause)
        btn_row1.addWidget(self.btn_pause)
        ctrl_layout.addLayout(btn_row1)

        # Freeze / Snapshot button
        self.btn_freeze = QtWidgets.QPushButton(self.tr("📸 Freeze / Snapshot to Label"))
        self.btn_freeze.setStyleSheet(
            "QPushButton { background-color: #0288d1; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #039be5; }"
        )
        self.btn_freeze.setToolTip(self.tr("Freeze the current frame and load all detections into the canvas for editing"))
        self.btn_freeze.setEnabled(False)
        self.btn_freeze.clicked.connect(self._on_freeze_clicked)
        ctrl_layout.addWidget(self.btn_freeze)

        # Auto-Save Interval Option
        auto_save_box = QtWidgets.QHBoxLayout()
        self.check_auto_save = QtWidgets.QCheckBox(self.tr("Auto-Save Every:"))
        self.check_auto_save.toggled.connect(self._on_auto_save_toggled)
        auto_save_box.addWidget(self.check_auto_save)

        self.spin_interval = QtWidgets.QDoubleSpinBox()
        self.spin_interval.setRange(0.5, 60.0)
        self.spin_interval.setValue(2.0)
        self.spin_interval.setSuffix(" s")
        self.spin_interval.valueChanged.connect(self._on_auto_save_interval_changed)
        auto_save_box.addWidget(self.spin_interval)
        ctrl_layout.addLayout(auto_save_box)

        layout.addWidget(ctrl_group)

        # ----------------- Section 5: Telemetry HUD -----------------
        telemetry_group = QtWidgets.QGroupBox(self.tr("5. Real-Time Telemetry HUD"))
        tel_layout = QtWidgets.QGridLayout(telemetry_group)

        tel_layout.addWidget(QtWidgets.QLabel(self.tr("Camera FPS:")), 0, 0)
        self.lbl_fps = QtWidgets.QLabel("0.0")
        self.lbl_fps.setStyleSheet("font-weight: bold; color: #4caf50;")
        tel_layout.addWidget(self.lbl_fps, 0, 1)

        tel_layout.addWidget(QtWidgets.QLabel(self.tr("Inference FPS:")), 0, 2)
        self.lbl_infer_fps = QtWidgets.QLabel("0.0")
        self.lbl_infer_fps.setStyleSheet("font-weight: bold; color: #2196f3;")
        tel_layout.addWidget(self.lbl_infer_fps, 0, 3)

        tel_layout.addWidget(QtWidgets.QLabel(self.tr("Latency:")), 1, 0)
        self.lbl_latency = QtWidgets.QLabel("0.0 ms")
        tel_layout.addWidget(self.lbl_latency, 1, 1)

        tel_layout.addWidget(QtWidgets.QLabel(self.tr("Objects:")), 1, 2)
        self.lbl_objects = QtWidgets.QLabel("0")
        self.lbl_objects.setStyleSheet("font-weight: bold; color: #ff9800;")
        tel_layout.addWidget(self.lbl_objects, 1, 3)

        tel_layout.addWidget(QtWidgets.QLabel(self.tr("Resolution:")), 2, 0)
        self.lbl_resolution = QtWidgets.QLabel("N/A")
        tel_layout.addWidget(self.lbl_resolution, 2, 1, 1, 3)

        layout.addWidget(telemetry_group)
        layout.addStretch()

        self.setWidget(main_widget)

    def _connect_signals(self):
        self.camera_service.camera_started.connect(self._on_camera_started)
        self.camera_service.camera_stopped.connect(self._on_camera_stopped)
        self.camera_service.frame_ready.connect(self._on_frame_ready)
        self.camera_service.camera_error.connect(self._on_camera_error)

    def _refresh_cameras(self):
        current_data = self.device_combo.currentData()
        self.device_combo.clear()
        cams = LiveCameraService.scan_available_cameras()
        for idx in cams:
            self.device_combo.addItem(f"Camera {idx}", idx)
        if current_data in cams:
            self.device_combo.setCurrentIndex(cams.index(current_data))

    def _on_mode_changed(self, index: int):
        mode = self.mode_combo.currentData()
        self.view_mode_changed.emit(mode)

    def _on_resolution_changed(self, index: int):
        name = self.res_combo.currentText()
        if name in RESOLUTION_PRESETS:
            w, h = RESOLUTION_PRESETS[name]
            self.camera_service.set_resolution(w, h)

    def _on_thresholds_changed(self):
        self.camera_service.set_thresholds(
            self.conf_spin.value(),
            self.iou_spin.value()
        )

    def _on_model_selected(self, index: int):
        val = self.model_combo.currentData()
        self.model_quick_switched.emit(str(val))

    def _toggle_camera(self):
        if self.camera_service.is_running:
            self.camera_service.stop_camera()
        else:
            url = self.stream_url_input.text().strip()
            device = url if url else self.device_combo.currentData()
            res_name = self.res_combo.currentText()
            resolution = RESOLUTION_PRESETS.get(res_name, (1920, 1080))
            self.camera_service.start_camera(device, resolution)

    def _toggle_pause(self):
        paused = self.camera_service.toggle_pause()
        self.btn_pause.setText(self.tr("Resume") if paused else self.tr("Pause"))

    def _on_freeze_clicked(self):
        self.freeze_snapshot_requested.emit()

    def _on_auto_save_toggled(self, checked: bool):
        self.camera_service.auto_save_enabled = checked

    def _on_auto_save_interval_changed(self, val: float):
        self.camera_service.auto_save_interval = val

    def _on_camera_started(self, w: int, h: int):
        self.btn_toggle_camera.setText(self.tr("Stop Camera"))
        self.btn_toggle_camera.setStyleSheet(
            "QPushButton { background-color: #c62828; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #d32f2f; }"
        )
        self.btn_pause.setEnabled(True)
        self.btn_pause.setText(self.tr("Pause"))
        self.btn_freeze.setEnabled(True)
        self.lbl_resolution.setText(f"{w} x {h}")

    def _on_camera_stopped(self):
        self.btn_toggle_camera.setText(self.tr("Start Camera"))
        self.btn_toggle_camera.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #388e3c; }"
        )
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText(self.tr("Pause"))
        self.btn_freeze.setEnabled(False)
        self.lbl_fps.setText("0.0")
        self.lbl_infer_fps.setText("0.0")
        self.lbl_latency.setText("0.0 ms")
        self.lbl_objects.setText("0")
        self.lbl_resolution.setText("N/A")

    def _on_frame_ready(self, qimage: QtGui.QImage, shapes: list, stats: dict):
        self.lbl_fps.setText(f"{stats.get('fps', 0.0):.1f}")
        self.lbl_infer_fps.setText(f"{stats.get('infer_fps', 0.0):.1f}")
        self.lbl_latency.setText(f"{stats.get('latency_ms', 0.0):.1f} ms")
        self.lbl_objects.setText(str(stats.get('count', 0)))
        if "width" in stats and "height" in stats:
            self.lbl_resolution.setText(f"{stats['width']} x {stats['height']}")

    def _on_camera_error(self, err_msg: str):
        QtWidgets.QMessageBox.warning(
            self,
            self.tr("Camera Error"),
            self.tr(f"Could not connect to camera:\n\n{err_msg}")
        )

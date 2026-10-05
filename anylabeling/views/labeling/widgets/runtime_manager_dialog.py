import os
import sys
import subprocess
import threading
from typing import List

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal

from anylabeling.views.labeling.logger import logger


class RuntimeManagerDialog(QtWidgets.QDialog):
    """
    Voicebox-style Hardware Acceleration and Runtime Manager Dialog.
    Detects hardware, manages CPU / DirectML / CUDA providers,
    and provides 1-click runtime installation.
    """

    provider_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Hardware Acceleration & Runtime Manager"))
        self.setMinimumWidth(560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._init_ui()
        self._detect_hardware()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Header info
        title = QtWidgets.QLabel(self.tr("⚡ Hardware Inference Acceleration"))
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2;")
        layout.addWidget(title)

        desc = QtWidgets.QLabel(
            self.tr("Select or install optimized runtimes for high-speed live object detection.")
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Hardware Detection Box
        hw_group = QtWidgets.QGroupBox(self.tr("Detected System Hardware"))
        hw_layout = QtWidgets.QFormLayout(hw_group)

        self.lbl_cpu = QtWidgets.QLabel(self._get_cpu_name())
        self.lbl_cpu.setStyleSheet("font-weight: bold;")
        hw_layout.addRow(self.tr("Processor:"), self.lbl_cpu)

        self.lbl_gpu = QtWidgets.QLabel(self.tr("Scanning..."))
        self.lbl_gpu.setStyleSheet("font-weight: bold; color: #2e7d32;")
        hw_layout.addRow(self.tr("Graphics Card:"), self.lbl_gpu)

        self.lbl_active_provider = QtWidgets.QLabel(self.tr("Checking..."))
        self.lbl_active_provider.setStyleSheet("font-weight: bold; color: #0288d1;")
        hw_layout.addRow(self.tr("Active ONNX Provider:"), self.lbl_active_provider)

        layout.addWidget(hw_group)

        # Runtimes Selection & Installation Box
        runtime_group = QtWidgets.QGroupBox(self.tr("Execution Providers"))
        rt_layout = QtWidgets.QVBoxLayout(runtime_group)

        self.btn_group = QtWidgets.QButtonGroup(self)

        # 1. CPU Mode
        self.rb_cpu = QtWidgets.QRadioButton(self.tr("CPU Mode (Universal Compatibility)"))
        self.rb_cpu.setChecked(True)
        self.btn_group.addButton(self.rb_cpu, 1)
        rt_layout.addWidget(self.rb_cpu)
        rt_layout.addWidget(QtWidgets.QLabel(self.tr("   Runs reliably on any Windows PC without requiring dedicated GPU drivers.")))

        rt_layout.addSpacing(6)

        # 2. DirectML Mode
        self.rb_dml = QtWidgets.QRadioButton(self.tr("DirectML GPU Mode (AMD, Intel Arc, NVIDIA)"))
        self.btn_group.addButton(self.rb_dml, 2)
        rt_layout.addWidget(self.rb_dml)
        rt_layout.addWidget(QtWidgets.QLabel(self.tr("   Hardware GPU acceleration across all Windows GPUs via DirectX 12.")))

        rt_layout.addSpacing(6)

        # 3. CUDA Mode
        self.rb_cuda = QtWidgets.QRadioButton(self.tr("NVIDIA CUDA Mode (Maximum NVIDIA Performance)"))
        self.btn_group.addButton(self.rb_cuda, 3)
        rt_layout.addWidget(self.rb_cuda)
        rt_layout.addWidget(QtWidgets.QLabel(self.tr("   Ultra-low latency inference for NVIDIA GeForce RTX / GTX cards.")))

        layout.addWidget(runtime_group)

        # 1-Click Install Button & Progress
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Marquee mode
        layout.addWidget(self.progress_bar)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: #757575;")
        layout.addWidget(self.status_label)

        # Action Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_install = QtWidgets.QPushButton(self.tr("Apply / 1-Click Install Selected Runtime"))
        self.btn_install.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1565c0; }"
        )
        self.btn_install.clicked.connect(self._apply_runtime)
        btn_layout.addWidget(self.btn_install)

        btn_close = QtWidgets.QPushButton(self.tr("Close"))
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _get_cpu_name(self) -> str:
        try:
            import platform
            return platform.processor() or "x86_64 Compatible"
        except Exception:
            return "Windows PC"

    def _detect_hardware(self):
        # 1. Detect GPU via PowerShell WMI or PyTorch/ONNX
        gpu_name = "Integrated / Standard Display"
        try:
            cmd = "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd], text=True, timeout=3)
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            if lines:
                gpu_name = ", ".join(lines)
        except Exception:
            pass
        self.lbl_gpu.setText(gpu_name)

        # 2. Detect ONNX Runtime providers
        providers = []
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
        except Exception:
            pass

        self.lbl_active_provider.setText(", ".join(providers) if providers else "CPUExecutionProvider")

        if "CUDAExecutionProvider" in providers:
            self.rb_cuda.setChecked(True)
        elif "DmlExecutionProvider" in providers:
            self.rb_dml.setChecked(True)
        else:
            self.rb_cpu.setChecked(True)

    def _apply_runtime(self):
        selected_id = self.btn_group.checkedId()
        if selected_id == 1:
            # CPU
            self.status_label.setText(self.tr("Active runtime set to CPU."))
            self.provider_changed.emit("cpu")
            QtWidgets.QMessageBox.information(
                self, self.tr("Runtime Applied"), self.tr("Inference will use CPU execution provider.")
            )
        elif selected_id == 2:
            # DirectML
            self._install_package_async("onnxruntime-directml", "directml")
        elif selected_id == 3:
            # CUDA
            self._install_package_async("onnxruntime-gpu", "cuda")

    def _install_package_async(self, package_name: str, provider_key: str):
        self.progress_bar.setVisible(True)
        self.btn_install.setEnabled(False)
        self.status_label.setText(self.tr(f"Installing {package_name} in background..."))

        def worker():
            err = None
            try:
                # pip install
                cmd = [sys.executable, "-m", "pip", "install", package_name]
                subprocess.check_call(cmd, timeout=180)
            except Exception as e:
                err = str(e)

            QtCore.QMetaObject.invokeMethod(
                self,
                "_on_install_completed",
                Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, provider_key),
                QtCore.Q_ARG(str, err or ""),
            )

        threading.Thread(target=worker, daemon=True).start()

    @QtCore.pyqtSlot(str, str)
    def _on_install_completed(self, provider_key: str, error_msg: str):
        self.progress_bar.setVisible(False)
        self.btn_install.setEnabled(True)

        if error_msg:
            self.status_label.setText(self.tr(f"Installation failed: {error_msg}"))
            QtWidgets.QMessageBox.warning(
                self, self.tr("Installation Notice"), self.tr(f"Could not install package automatically:\n\n{error_msg}")
            )
        else:
            self.status_label.setText(self.tr("Hardware acceleration package installed successfully!"))
            self.provider_changed.emit(provider_key)
            self._detect_hardware()
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Acceleration Ready"),
                self.tr("Hardware acceleration runtime installed! Your live detection will now use hardware GPU inference."),
            )

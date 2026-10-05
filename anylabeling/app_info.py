__appname__ = "LiveObjectDetection"
__appdescription__ = "High-performance real-time camera object detection, live tracking, and AI annotation studio powered by PyTorch, ONNX, DirectML, and YOLO/RT-DETR/SAM model zoos."
__version__ = "1.0.0"
__url__ = "https://github.com/VicRoger27/LiveObjectDetection"

CLI_HELP_MSG = """
    Usage: liveobjectdetection [COMMAND] [OPTIONS]

    Available Commands:
        help              Show this help message
        checks            Display system, camera and package information
        version           Show version information
        config            Show config file path
        convert           Run conversion tasks

    Launch Options:
        liveobjectdetection                                Launch the GUI application
        liveobjectdetection --filename IMAGE/VIDEO         Open specific image or video
        liveobjectdetection --output DIR                   Set output directory
        liveobjectdetection --config FILE                  Use custom config file
        liveobjectdetection --reset-config                 Reset Qt config
        liveobjectdetection --qt-image-allocation-limit 1024  Set Qt image allocation limit to 1024 MB

    Conversion Tasks:
        liveobjectdetection convert                        List all conversion tasks
        liveobjectdetection convert --task <task>          Show help for a specific task
        liveobjectdetection convert --task <task> [opts]   Run conversion

    Features:
        - Real-Time Live Webcam & RTSP Object Detection
        - Integrated Canvas, Continuous Monitor HUD, and Dual-Pane Modes
        - Freeze-to-Label (Spacebar) for instant dataset annotation
        - 1-Click Hardware Acceleration Manager (CPU / DirectML / CUDA)

    GitHub: https://github.com/VicRoger27/LiveObjectDetection
"""


def __getattr__(name):
    if name == "__preferred_device__":
        from anylabeling.views.common.device_manager import (
            get_preferred_device,
        )

        return get_preferred_device()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

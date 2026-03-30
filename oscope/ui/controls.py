from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from oscope.models.settings import TDIV_VALUES, VDIV_VALUES

# Color constants
CH1_COLOR = "#FFD700"  # yellow
CH2_COLOR = "#00E5FF"  # cyan
ACCENT_GREEN = "#a6e3a1"
ACCENT_RED = "#f38ba8"
ACCENT_BLUE = "#89b4fa"
ACCENT_PEACH = "#fab387"
ACCENT_MAUVE = "#cba6f7"

GROUPBOX_STYLE = """
QGroupBox {{
    border: 2px solid {color};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: bold;
    color: {color};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {color};
}}
"""

BUTTON_STYLE = """
QPushButton {{
    background-color: {bg};
    color: {fg};
    font-weight: bold;
    padding: 7px 12px;
    border: none;
    border-radius: 4px;
}}
QPushButton:hover {{
    background-color: {hover};
}}
QPushButton:disabled {{
    background-color: #45475a;
    color: #6c7086;
}}
"""


class ChannelGroup(QGroupBox):
    """Per-channel controls: V/div, coupling, probe."""

    vdiv_changed = pyqtSignal(int, float)       # channel, range_volts
    coupling_changed = pyqtSignal(int, str)     # channel, coupling
    probe_changed = pyqtSignal(int, float)      # channel, ratio

    def __init__(self, channel: int, color: str) -> None:
        super().__init__(f"CH{channel}")
        self._channel = channel
        self.setStyleSheet(GROUPBOX_STYLE.format(color=color))

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(6, 16, 6, 6)

        layout.addWidget(_colored_label("V/div", color))
        self.vdiv_combo = QComboBox()
        for label, _ in VDIV_VALUES:
            self.vdiv_combo.addItem(label)
        self.vdiv_combo.setCurrentIndex(8)  # default 1 V/div
        layout.addWidget(self.vdiv_combo)

        layout.addWidget(_colored_label("Coupling", color))
        self.coupling_combo = QComboBox()
        self.coupling_combo.addItems(["DC", "AC"])
        layout.addWidget(self.coupling_combo)

        layout.addWidget(_colored_label("Probe", color))
        self.probe_combo = QComboBox()
        self.probe_combo.addItems(["1:1", "10:1", "100:1"])
        layout.addWidget(self.probe_combo)

        # Wire signals
        self.vdiv_combo.currentIndexChanged.connect(self._on_vdiv)
        self.coupling_combo.currentTextChanged.connect(self._on_coupling)
        self.probe_combo.currentIndexChanged.connect(self._on_probe)

    def _on_vdiv(self, index: int) -> None:
        _, vdiv = VDIV_VALUES[index]
        self.vdiv_changed.emit(self._channel, vdiv * 8)

    def _on_coupling(self, text: str) -> None:
        self.coupling_changed.emit(self._channel, text)

    def _on_probe(self, index: int) -> None:
        ratios = [1.0, 10.0, 100.0]
        self.probe_changed.emit(self._channel, ratios[index])


def _colored_label(text: str, color: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
    return label


# Maps for trigger UI text -> SCPI values
TRIG_SOURCE_MAP = {
    "Channel 1": "CHANnel1",
    "Channel 2": "CHANnel2",
    "External": "EXTernal",
    "Line": "LINE",
}
TRIG_COUPLING_MAP = {"DC": "DC", "AC": "AC", "LF Reject": "LFReject", "HF Reject": "HFReject"}
TRIG_TV_MODE_MAP = {"Field 1": "FIEld1", "Field 2": "FIEld2", "Line": "LINE"}


class ControlPanel(QWidget):
    """Right-side control panel with per-channel, timebase, trigger, and action controls."""

    # Channel signals (forwarded from ChannelGroups)
    vdiv_changed = pyqtSignal(int, float)
    coupling_changed = pyqtSignal(int, str)
    probe_changed = pyqtSignal(int, float)

    # Timebase signals
    tdiv_changed = pyqtSignal(float)

    # Individual trigger signals — one per setting
    trig_sweep_changed = pyqtSignal(str)       # SCPI sweep value
    trig_source_changed = pyqtSignal(str)      # SCPI source value
    trig_level_changed = pyqtSignal(float)     # volts
    trig_slope_changed = pyqtSignal(str)       # SCPI slope value
    trig_coupling_changed = pyqtSignal(str)    # SCPI coupling value
    trig_nreject_changed = pyqtSignal(bool)
    trig_tv_mode_changed = pyqtSignal(str)     # SCPI TV mode value

    # Action signals
    acquire_clicked = pyqtSignal()
    run_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    autoscale_clicked = pyqtSignal()
    save_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setFixedWidth(290)

        # Use a scroll area so controls don't get clipped on small screens
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # --- Acquire channel selector ---
        acq_group = QGroupBox("Acquire")
        acq_group.setStyleSheet(GROUPBOX_STYLE.format(color=ACCENT_GREEN))
        acq_layout = QVBoxLayout(acq_group)
        acq_layout.addWidget(_colored_label("Source", ACCENT_GREEN))
        self.acq_channel_combo = QComboBox()
        self.acq_channel_combo.addItems(["Channel 1", "Channel 2", "Both"])
        acq_layout.addWidget(self.acq_channel_combo)
        layout.addWidget(acq_group)

        # --- CH1 and CH2 side by side ---
        ch_row = QHBoxLayout()
        self.ch1_group = ChannelGroup(1, CH1_COLOR)
        self.ch2_group = ChannelGroup(2, CH2_COLOR)
        ch_row.addWidget(self.ch1_group)
        ch_row.addWidget(self.ch2_group)
        layout.addLayout(ch_row)

        # Forward per-channel signals
        self.ch1_group.vdiv_changed.connect(self.vdiv_changed)
        self.ch1_group.coupling_changed.connect(self.coupling_changed)
        self.ch1_group.probe_changed.connect(self.probe_changed)
        self.ch2_group.vdiv_changed.connect(self.vdiv_changed)
        self.ch2_group.coupling_changed.connect(self.coupling_changed)
        self.ch2_group.probe_changed.connect(self.probe_changed)

        # --- Timebase group ---
        tb_group = QGroupBox("Timebase")
        tb_group.setStyleSheet(GROUPBOX_STYLE.format(color=ACCENT_BLUE))
        tb_layout = QVBoxLayout(tb_group)

        tb_layout.addWidget(_colored_label("Time/div", ACCENT_BLUE))
        self.tdiv_combo = QComboBox()
        for label, _ in TDIV_VALUES:
            self.tdiv_combo.addItem(label)
        self.tdiv_combo.setCurrentIndex(16)  # default 1 ms/div
        tb_layout.addWidget(self.tdiv_combo)

        layout.addWidget(tb_group)

        # --- Trigger group ---
        trig_group = QGroupBox("Trigger")
        trig_group.setStyleSheet(GROUPBOX_STYLE.format(color=ACCENT_PEACH))
        trig_layout = QVBoxLayout(trig_group)

        trig_layout.addWidget(_colored_label("Mode", ACCENT_PEACH))
        self.sweep_combo = QComboBox()
        self.sweep_combo.addItems(["Auto Level", "Auto", "Normal", "Single", "TV"])
        trig_layout.addWidget(self.sweep_combo)

        trig_layout.addWidget(_colored_label("Source", ACCENT_PEACH))
        self.trig_source_combo = QComboBox()
        self.trig_source_combo.addItems(["Channel 1", "Channel 2", "External", "Line"])
        trig_layout.addWidget(self.trig_source_combo)

        trig_layout.addWidget(_colored_label("Level (V)", ACCENT_PEACH))
        self.trig_level_spin = QDoubleSpinBox()
        self.trig_level_spin.setRange(-10.0, 10.0)
        self.trig_level_spin.setSingleStep(0.1)
        self.trig_level_spin.setDecimals(3)
        trig_layout.addWidget(self.trig_level_spin)

        trig_layout.addWidget(_colored_label("Slope", ACCENT_PEACH))
        self.trig_slope_combo = QComboBox()
        self.trig_slope_combo.addItems(["Rising", "Falling"])
        trig_layout.addWidget(self.trig_slope_combo)

        trig_layout.addWidget(_colored_label("Coupling", ACCENT_PEACH))
        self.trig_coupling_combo = QComboBox()
        self.trig_coupling_combo.addItems(["DC", "AC", "LF Reject", "HF Reject"])
        trig_layout.addWidget(self.trig_coupling_combo)

        self.noise_reject_check = QCheckBox("Noise Reject")
        self.noise_reject_check.setStyleSheet(f"color: {ACCENT_PEACH};")
        trig_layout.addWidget(self.noise_reject_check)

        self.tv_mode_label = _colored_label("TV Mode", ACCENT_PEACH)
        self.tv_mode_combo = QComboBox()
        self.tv_mode_combo.addItems(["Field 1", "Field 2", "Line"])
        trig_layout.addWidget(self.tv_mode_label)
        trig_layout.addWidget(self.tv_mode_combo)
        self.tv_mode_label.setVisible(False)
        self.tv_mode_combo.setVisible(False)

        layout.addWidget(trig_group)

        # --- Actions group ---
        act_group = QGroupBox("Actions")
        act_group.setStyleSheet(GROUPBOX_STYLE.format(color=ACCENT_MAUVE))
        act_layout = QVBoxLayout(act_group)

        self.acquire_btn = QPushButton("Acquire")
        self.acquire_btn.setStyleSheet(BUTTON_STYLE.format(
            bg=ACCENT_GREEN, fg="#1e1e2e", hover="#94e2d5"
        ))
        act_layout.addWidget(self.acquire_btn)

        self.run_btn = QPushButton("Run")
        self.run_btn.setStyleSheet(BUTTON_STYLE.format(
            bg=ACCENT_BLUE, fg="#1e1e2e", hover="#b4d0fb"
        ))
        act_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(BUTTON_STYLE.format(
            bg=ACCENT_RED, fg="#1e1e2e", hover="#f5a0b8"
        ))
        act_layout.addWidget(self.stop_btn)

        self.autoscale_btn = QPushButton("Autoscale")
        self.autoscale_btn.setStyleSheet(BUTTON_STYLE.format(
            bg=ACCENT_PEACH, fg="#1e1e2e", hover="#fbc4a0"
        ))
        act_layout.addWidget(self.autoscale_btn)

        self.save_btn = QPushButton("Save CSV...")
        self.save_btn.setStyleSheet(BUTTON_STYLE.format(
            bg=ACCENT_MAUVE, fg="#1e1e2e", hover="#d5b8f9"
        ))
        act_layout.addWidget(self.save_btn)

        layout.addWidget(act_group)
        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # --- Connect signals ---
        self.tdiv_combo.currentIndexChanged.connect(self._on_tdiv_changed)

        # Individual trigger signals — only send the specific command that changed
        self.sweep_combo.currentTextChanged.connect(self._on_sweep_changed)
        self.trig_source_combo.currentTextChanged.connect(self._on_trig_source)
        self.trig_level_spin.valueChanged.connect(self.trig_level_changed.emit)
        self.trig_slope_combo.currentTextChanged.connect(self._on_trig_slope)
        self.trig_coupling_combo.currentTextChanged.connect(self._on_trig_coupling)
        self.noise_reject_check.toggled.connect(self.trig_nreject_changed.emit)
        self.tv_mode_combo.currentTextChanged.connect(self._on_trig_tv_mode)

        self.acquire_btn.clicked.connect(self.acquire_clicked.emit)
        self.run_btn.clicked.connect(self.run_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.autoscale_btn.clicked.connect(self.autoscale_clicked.emit)
        self.save_btn.clicked.connect(self.save_clicked.emit)

    @property
    def current_channel(self) -> int | list[int]:
        """Returns 1, 2, or [1, 2] for 'Both'."""
        idx = self.acq_channel_combo.currentIndex()
        if idx == 2:
            return [1, 2]
        return idx + 1

    # --- Internal handlers ---

    def _on_tdiv_changed(self, index: int) -> None:
        _, tdiv = TDIV_VALUES[index]
        self.tdiv_changed.emit(tdiv * 10)

    def _on_sweep_changed(self, text: str) -> None:
        # Show/hide TV controls
        is_tv = text == "TV"
        self.tv_mode_label.setVisible(is_tv)
        self.tv_mode_combo.setVisible(is_tv)

        # Map to SCPI
        sweep_map = {"Auto Level": "AUTO", "Auto": "AUTO", "Normal": "NORMal", "Single": "SINGle", "TV": "NORMal"}
        self.trig_sweep_changed.emit(sweep_map[text])

    def _on_trig_source(self, text: str) -> None:
        self.trig_source_changed.emit(TRIG_SOURCE_MAP[text])

    def _on_trig_slope(self, text: str) -> None:
        self.trig_slope_changed.emit("POSitive" if text == "Rising" else "NEGative")

    def _on_trig_coupling(self, text: str) -> None:
        self.trig_coupling_changed.emit(TRIG_COUPLING_MAP[text])

    def _on_trig_tv_mode(self, text: str) -> None:
        self.trig_tv_mode_changed.emit(TRIG_TV_MODE_MAP[text])

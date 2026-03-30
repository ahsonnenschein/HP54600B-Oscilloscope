# HP 54600B Oscilloscope Controller

A desktop application for controlling and acquiring waveforms from an HP 54600B oscilloscope via GPIB, using a Xyphro USB-GPIB adapter.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Dual-channel acquisition** — acquire from Channel 1, Channel 2, or both simultaneously with independent color-coded traces (CH1 = yellow, CH2 = cyan)
- **Independent channel controls** — separate V/div, AC/DC coupling, and probe ratio for each channel, just like the real front panel
- **Full trigger control** — Auto Level, Auto, Normal, Single, and TV trigger modes with edge settings (source, level, slope, coupling, noise reject)
- **Continuous acquisition** — Run mode for live waveform updates, Stop to freeze
- **Timebase control** — 5 ns/div to 5 s/div
- **CSV export** — save waveform data with full metadata header; dual-channel saves create separate files per channel
- **Dark oscilloscope-style UI** — Catppuccin Mocha theme with pyqtgraph waveform display, crosshair cursor, trigger marker, and color-coded control groups
- **Auto-detection** — automatically finds the oscilloscope on any GPIB address
- **Thread-safe** — all GPIB communication runs on a dedicated worker thread with a command queue

## Requirements

### Hardware

- HP 54600B oscilloscope (or compatible 54600-series)
- HP 54650A GPIB interface module installed in the scope
- [Xyphro USB-GPIB adapter](https://usbgpib.com/) (V2, USBTMC)

### Software

- Python 3.10+
- Linux (tested on Ubuntu)

## Installation

```bash
git clone https://github.com/ahsonnenschein/oscilloscope.git
cd oscilloscope
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### USB permissions (Linux)

The Xyphro adapter needs a udev rule so it's accessible without root:

```bash
sudo cp 99-xyphro-gpib.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Verify with `ls -la /dev/usbtmc*` — it should show `crw-rw-rw-` permissions.

## Usage

```bash
source venv/bin/activate
python main.py
```

1. Click **Connect** — the app auto-detects the oscilloscope
2. Set channel V/div, coupling, and timebase as needed
3. Click **Acquire** for a single capture, or **Run** for continuous acquisition
4. Click **Stop** to freeze the display
5. Click **Save CSV...** to export waveform data

## Project Structure

```
oscilloscope/
    main.py                     # Entry point, dark theme
    requirements.txt
    99-xyphro-gpib.rules        # Udev rule for Xyphro adapter
    oscope/
        gpib/
            connection.py       # VISA resource management, auto-detection
            commands.py         # HP 54600B SCPI command API
            worker.py           # QThread worker with command queue
            protocol.py         # IEEE 488.2 binary block parsing
        models/
            waveform.py         # WaveformData, PreambleData dataclasses
            settings.py         # Settings dataclasses, V/div and T/div tables
        ui/
            mainwindow.py       # Main window, signal/slot wiring
            waveform_plot.py    # pyqtgraph oscilloscope display
            controls.py         # Channel, timebase, trigger, action controls
            connection_bar.py   # Connection toolbar with status LED
            dialogs.py          # File dialog helpers
        export/
            csv_writer.py       # CSV export with metadata
```

## Architecture

```
UI Layer (PyQt6, main thread)
    | signals/slots
Worker Layer (QThread, command queue)
    | pyvisa calls
GPIB Layer (pyvisa-py, USBTMC)
    | USB
Xyphro Adapter → HP 54600B
```

All VISA calls run exclusively on the worker thread. The UI enqueues commands and receives results via Qt signals carrying immutable dataclasses.

## License

MIT

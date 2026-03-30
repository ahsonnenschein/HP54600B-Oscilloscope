from __future__ import annotations

import pyvisa


class GpibConnection:
    """Manages VISA resource discovery and connection to the HP 54600B."""

    def __init__(self) -> None:
        self._rm: pyvisa.ResourceManager | None = None
        self._instrument: pyvisa.resources.Resource | None = None
        self._idn: str = ""

    @property
    def instrument(self) -> pyvisa.resources.Resource:
        if self._instrument is None:
            raise RuntimeError("Not connected")
        return self._instrument

    @property
    def is_connected(self) -> bool:
        return self._instrument is not None

    @property
    def idn(self) -> str:
        return self._idn

    def detect_and_connect(self) -> str:
        """Auto-detect and connect to the HP 54600B. Returns IDN string."""
        # Close any previous connection first
        self.disconnect()

        self._rm = pyvisa.ResourceManager("@py")

        # Try USB USBTMC resources first (Xyphro adapter)
        resources = list(self._rm.list_resources("USB?*INSTR"))
        # Also try GPIB resources in case the backend maps them
        resources += list(self._rm.list_resources("GPIB?*INSTR"))

        # If nothing found, try scanning GPIB addresses directly
        if not resources:
            resources = [f"GPIB0::{addr}::INSTR" for addr in range(31)]

        last_error = ""
        for resource_str in resources:
            try:
                instr = self._rm.open_resource(resource_str)
                instr.read_termination = "\n"
                instr.write_termination = "\n"
                instr.timeout = 5000

                # Send device clear to recover from any stuck state
                try:
                    instr.clear()
                except Exception:
                    pass

                import time
                time.sleep(0.5)

                # HP quirk: first command after connect may fail silently
                try:
                    idn = instr.query("*IDN?")
                except Exception:
                    try:
                        instr.clear()
                    except Exception:
                        pass
                    time.sleep(0.3)
                    idn = instr.query("*IDN?")

                idn = idn.strip()
                if "54600" in idn or "HEWLETT" in idn.upper() or "54601" in idn:
                    instr.timeout = 35000  # long timeout for :DIGitize
                    self._instrument = instr
                    self._idn = idn
                    return idn
                else:
                    instr.close()
            except Exception as e:
                last_error = str(e)
                try:
                    instr.close()  # type: ignore[possibly-undefined]
                except Exception:
                    pass

        raise ConnectionError(
            f"HP 54600B not found on any GPIB/USB address. Last error: {last_error}"
        )

    def disconnect(self) -> None:
        """Close the VISA resource."""
        if self._instrument is not None:
            try:
                self._instrument.close()
            except Exception:
                pass
            self._instrument = None
            self._idn = ""
        if self._rm is not None:
            try:
                self._rm.close()
            except Exception:
                pass
            self._rm = None

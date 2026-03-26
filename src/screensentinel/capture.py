from __future__ import annotations

from pathlib import Path

from mss import mss


class ScreenCapture:
    def capture_primary(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with mss() as sct:
            # mss.shot expects a monitor index for mon=...
            sct.shot(mon=1, output=str(output_path))
        return output_path

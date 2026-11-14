"""Retired integrations: explain the removal and clean up what older versions left running."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
import time

from honey import paths

DELTA_LABEL = "dev.honey.delta-capture"


def delta_plist(home=None) -> str:
    return os.path.join(home or os.path.expanduser("~"), "Library", "LaunchAgents", DELTA_LABEL + ".plist")


def retire_delta_service(home=None, backups=None) -> str | None:
    """Move the old Delta capture LaunchAgent to backups and unload it. Returns the backup path, if any."""
    plist = delta_plist(home)
    if not os.path.isfile(plist):
        return None
    dst = os.path.join(backups or paths.path("backups", time.strftime("%Y%m%dT%H%M%S")), "launch-agents", os.path.basename(plist))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(plist, dst)
    if sys.platform == "darwin" and home is None:
        # Last step: when launchd itself ran this command, bootout ends this process.
        try:
            subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{DELTA_LABEL}"], capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            pass  # the definition is already gone, so launchd won't start it again after logout
    return dst


def delta(argv: list) -> int:
    print("honey delta was removed from honey-stack. Use the Delta CLI directly (https://delta.dev/cli) if you still need history.",
          file=sys.stderr)
    moved = retire_delta_service()
    if moved:
        print(f"Stopped the old Delta capture service; its definition was moved to {moved}.", file=sys.stderr)
    print("Captured data under ~/.honey/delta is no longer read and can be deleted.", file=sys.stderr)
    return 2

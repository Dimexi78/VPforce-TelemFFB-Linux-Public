#!/usr/bin/env python3
"""Forward Falcon BMS shared-memory telemetry to native TelemFFB over UDP.

Run this process *inside the same Wine prefix as Falcon BMS*.  It intentionally
keeps all Win32 mapping access on the Wine side; the Linux application only
receives ordinary UDP frames.
"""

import argparse
import logging
import socket
import time

from wine.telemffb.telem.BMSTelemManager import BMSManager


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=34382, type=int)
    parser.add_argument("--rate", default=60.0, type=float,
                        help="maximum send rate in Hz")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    manager = BMSManager()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    period = 1.0 / max(args.rate, 1.0)
    logging.info("Forwarding Falcon BMS telemetry to %s:%d", args.host, args.port)
    try:
        while True:
            started = time.monotonic()
            frame = manager.process_packet(b"")
            if frame:
                sock.sendto(frame, (args.host, args.port))
            time.sleep(max(0.0, period - (time.monotonic() - started)))
    except KeyboardInterrupt:
        return 0
    finally:
        sock.close()
        manager.bms_memory.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())

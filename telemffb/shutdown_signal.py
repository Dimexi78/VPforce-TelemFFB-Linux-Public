"""Translate SIGTERM into a normal Qt shutdown, including device cleanup."""

import signal

from PyQt6.QtCore import QTimer


def install_shutdown_handler(app):
    """Arrange for SIGTERM to leave the event loop on the Qt main thread."""
    requested = False

    def request_shutdown(_signum, _frame):
        nonlocal requested
        requested = True

    def check_shutdown():
        if requested:
            app.quit()

    signal.signal(signal.SIGTERM, request_shutdown)
    timer = QTimer(app)
    timer.timeout.connect(check_shutdown)
    timer.start(200)
    return timer

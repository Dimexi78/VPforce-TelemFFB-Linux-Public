"""Linux-only system settings dialog.

The upstream dialog was primarily a Windows installer/control panel for
DirectInput, game DLL injection, MSFS and Registry-backed discovery.  This
small dialog keeps the settings needed to use native HID plus DCS/BMS UDP.
"""

from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QLineEdit, QMessageBox, QVBoxLayout)

import telemffb.globals as G
from telemffb.hw.ffb_rhino import FFBRhino
from telemffb.utils import device_pid_key


class SystemSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TelemFFB System Settings")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.enable_dcs = QCheckBox()
        self.enable_bms = QCheckBox()
        self.enable_dcs.setChecked(bool(G.system_settings.get("enableDCS", False)))
        self.enable_bms.setChecked(bool(G.system_settings.get("enableBMS", False)))
        self.bms_port = QLineEdit(str(G.system_settings.get("portBMS", 34382)))
        self.device_role = QComboBox()
        self.device_role.addItems(["joystick", "pedals", "collective", "trimwheel"])
        self.device_role.setCurrentText(G.device_type or "joystick")
        self.device_pid = QComboBox()
        self._load_devices()
        form.addRow("Enable DCS UDP (34380)", self.enable_dcs)
        form.addRow("Enable Falcon BMS UDP", self.enable_bms)
        form.addRow("BMS UDP port", self.bms_port)
        form.addRow("Device role", self.device_role)
        form.addRow("VPforce HID device", self.device_pid)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_devices(self):
        devices = FFBRhino.enumerate()
        for dev in devices:
            self.device_pid.addItem(
                f"{dev.product_string} ({dev.vendor_id:04x}:{dev.product_id:04x})",
                (dev.product_id, dev.path.decode(errors="replace")),
            )
        if not devices:
            self.device_pid.addItem("No VPforce HID device detected", None)

    def _save(self):
        try:
            port = int(self.bms_port.text())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid port", "BMS UDP port must be 1–65535.")
            return
        role = self.device_role.currentText()
        selected = self.device_pid.currentData()
        if selected:
            pid, path = selected
            G.system_settings.setValue(device_pid_key(role), f"{pid:04x}")
            G.system_settings.setValue(f"devpath_{role}", path)
        G.system_settings.setValue("enableDCS", self.enable_dcs.isChecked())
        G.system_settings.setValue("enableBMS", self.enable_bms.isChecked())
        G.system_settings.setValue("portBMS", port)
        G.system_settings.sync()
        self.accept()

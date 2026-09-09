#
# This file is part of the TelemFFB distribution (https://github.com/walmis/TelemFFB).
# Copyright (c) 2023 Valmantas Palikša.
# Copyright (c) 2023 Micah Frisby
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import logging
import os
from typing import List, Optional, override

from PyQt6 import QtCore

import telemffb.globals as G
import telemffb.utils as utils
from telemffb.telem.IL2Manager import IL2TelemParser
from telemffb.telem.NetworkThread import NetworkThread
from telemffb.telem.UDPForwarder import IL2PacketForwarder


class SimTelemListener(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, name : str):
        super().__init__()
        self.name : str = name
        self.telem : NetworkThread = None
        self._started = False

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError

    def do_validate(self) -> bool:
        if G.child_instance:
            return None
        if G.system_settings.get(f'validate{self.name}'):
            self.validate()
            return True
        return False

    @property
    def started(self) -> bool:
        return self._started

    @started.setter
    def started(self, value : bool):
        """
        Mark instance as started, will emit a stateChanged signal on change
        """
        if bool(self._started) ^ bool(value):
            self._started = value
            self.stateChanged.emit(value)

    @property
    def is_enabled(self) -> bool:
        return bool(G.system_settings.get(f'enable{self.name}') or G.args.sim == self.name)

    @property
    def port_udp(self):
        port = int(G.system_settings.get(f'port{self.name}'))
        assert port
        return port


class SimIL2(SimTelemListener):
    def __init__(self) -> None:
        super().__init__("IL2")
        self._forwarder = IL2PacketForwarder()

    @override
    def start(self):
        if not self.is_enabled:
            return

        self.telem = NetworkThread(G.telem_manager, host="127.0.0.1", port=self.port_udp, telem_parser=IL2TelemParser(),
                                    raw_packet_hook=self._forwarder.forward)

        if self.do_validate() is False:
            logging.warning(
                "IL2 Config validation is disabled - please ensure the IL2 startup.cfg is configured correctly")

        if self.telem is None:  # stopped during validation (e.g. another sim won the race)
            return

        logging.info("Starting IL2 Telemetry Listener")
        self.telem.start()
        self.started = True

        if G.system_settings.get('validateIL2_K') and G.device_info:
            G.il2_ffb_device_ordinal = utils.resolve_il2_ffb_device_ordinal(
                G.system_settings.get('pathIL2_K'), G.device_info.vendor_id, G.device_info.product_id
            )

    @override
    def do_validate(self) -> bool:
        if G.child_instance:
            return None
        sturmovik = G.system_settings.get('validateIL2')
        korea = G.system_settings.get('validateIL2_K')
        if sturmovik or korea:
            self.validate()
            return True
        return False

    @override
    def validate(self):
        if G.system_settings.get('validateIL2'):
            il2_path = os.path.join(G.system_settings.get('pathIL2'), 'data\\startup.cfg')
            logging.info("Validating IL2 Sturmovik Telemetry Config")
            utils.analyze_il2_config(il2_path, port=self.port_udp, window=G.main_window, sim_name="IL-2 Sturmovik")
        if G.system_settings.get('validateIL2_K'):
            # Standalone: <root>\game\data; Steam (IL2Series): <root>\data.
            game_root = utils.il2_korea_game_root(G.system_settings.get('pathIL2_K'))
            il2_path = os.path.join(game_root, 'data', 'startup.cfg')
            logging.info("Validating IL2 Korea Telemetry Config")
            utils.analyze_il2_config(il2_path, port=self.port_udp, window=G.main_window, sim_name="IL-2 Korea", korea=True)

    @override
    def stop(self):
        logging.info("Stopping IL2 Telemetry Listener")
        if self.telem:
            self.telem.quit()
            self.telem = None
            self.started = False
        self._forwarder.close()


class SimBMS(SimTelemListener):
    def __init__(self) -> None:
        super().__init__("BMS")

    @override
    def start(self):
        if not self.is_enabled:
            return
        # Falcon BMS runs in Wine/Proton.  Its Win32 shared-memory mappings
        # are not visible to this native process, so a Windows-side exporter
        # must forward TelemFFB's normal semicolon-delimited frames over UDP.
        self.telem = NetworkThread(G.telem_manager, host="127.0.0.1",
                                   port=self.port_udp)
        logging.info("Starting BMS UDP telemetry listener on port %s", self.port_udp)
        self.telem.start()
        self.started = True

    @override
    def validate(self):
        return

    @override
    def stop(self):
        logging.info("Stopping BMS Telemetry Listener")
        if self.telem:
            self.telem.quit()
            self.telem = None
            self.started = False


class SimDCS(SimTelemListener):
    def __init__(self) -> None:
        super().__init__("DCS")
        self.telem_udp: Optional[NetworkThread] = None

    @override
    def start(self):
        if not self.is_enabled:
            return

        self.telem_udp = NetworkThread(G.telem_manager, host="0.0.0.0", port=34380)
        if self.telem_udp is None:
            return

        logging.info("Starting DCS Telemetry Listener")
        self.telem_udp.start()
        self.started = True

    @override
    def validate(self):
        logging.info("DCS exporter installation is manual on Linux; listening for UDP telemetry")

    @override
    def stop(self):
        logging.info("Stopping DCS Telemetry Listener")
        if self.telem_udp:
            self.telem_udp.quit()
            self.telem_udp = None
        self.started = False

class SimXPLANE(SimTelemListener):
    def __init__(self) -> None:
        super().__init__("XPLANE")
        self.telem : Optional[NetworkThread] = None

    @override
    def start(self):
        if not self.is_enabled:
            return

        self.telem = NetworkThread(G.telem_manager, host='127.0.0.1', port=34390)

        self.do_validate()

        if self.telem is None:
            return

        logging.info("Starting XPlane Telemetry Listener")

        self.telem.start()
        self.started = True

    @override
    def validate(self):
        logging.info("Checking XPlane Plugin")
        xplane_path = G.system_settings.get('pathXPLANE', '')
        utils.install_xplane_plugin(xplane_path, G.main_window)

    @override
    def stop(self):
        logging.info("Stopping XPlane Telemetry Listener")
        if self.telem:
            self.telem.quit()
            self.telem = None
            self.started = False

class SimMSFS(SimTelemListener):
    def __init__(self) -> None:
        super().__init__("MSFS")
        self.telem = None

    @override
    def start(self):
        if not self.is_enabled:
            return

        logging.warning("MSFS SimConnect is not included in the Linux-only build")

    @override
    def stop(self):
        logging.info("Stopping MSFS Telemetry Listener")
        self.started = False
    
    @override
    def validate(self):
        return

class SimListenerManager(QtCore.QObject):
    simStarted = QtCore.pyqtSignal(object)
    simStopped = QtCore.pyqtSignal(object)
    allStarted = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.sims : List[SimTelemListener] = [
            SimDCS(),
            SimMSFS(),
            SimIL2(),
            SimBMS(),
            SimXPLANE()
        ]

        for sim in self.sims:
            sim.stateChanged.connect(self._on_state_changed)

    def _on_state_changed(self, state):
        if state:
            self.simStarted.emit(self.sender())
        else:
            self.simStopped.emit(self.sender())

    def stop_inactive(self, active_sim):
        logging.info(f"Started receiving telemetry from {active_sim} - stopping other sim listeners")
        for sim in self.sims:
            if sim.name != active_sim:
                sim.stop()
    def start_all(self):
        self.allStarted.emit()
        for sim in self.sims:
            sim.start()

    def stop_all(self):
        for sim in self.sims:
            sim.stop()

    def restart_all(self):
        self.stop_all()
        self.start_all()

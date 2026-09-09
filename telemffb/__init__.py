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



#from .ButtonPressThread import ButtonPressThread
#from .LogTailWindow import LogTailWindow
#from .SystemSettingsDialog import SystemSettingsDialog

# ``typing.override`` was added in Python 3.12.  The project uses it widely,
# while this Linux fork supports Python 3.11 as documented.
import typing
if not hasattr(typing, "override"):
    from typing_extensions import override
    typing.override = override

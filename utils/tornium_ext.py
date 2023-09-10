# Copyright (C) 2021-2023 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import importlib
import logging
import pkgutil


class TorniumExt:
    def __init__(self, name):
        self.name: str = name

        try:
            self.package = importlib.import_module(self.name)
            self.loaded = True
        except Exception as e:
            logging.getLogger("server").warning(f"Tornium extension {self.name} failed to import with {e} raised")

            self.package = None
            self.loaded = False

        if self.loaded:
            try:
                self.extension = self.package.Extension()
            except AttributeError:
                self.package = None
                self.loaded = False
                self.extension = None
        else:
            self.extension = None

    @classmethod
    def from_package(cls, package: pkgutil.ModuleInfo):
        return cls(package.name)

    @classmethod
    def __iter__(cls):
        for package in pkgutil.iter_modules():
            if not package.name.startswith("tornium_"):
                continue
            elif package.name in ("tornium_commons", "tornium_celery"):
                continue

            yield cls.from_package(package)

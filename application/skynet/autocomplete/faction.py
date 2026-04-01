# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from tornium_commons.formatters import find_list
from tornium_commons.models import Faction


def faction_autocomplete(interaction, *args, **kwargs):
    # This is only intended to be the autocomplete for the faction parameter for the
    # `/faction data *` slash commands.
    # We want to find similr faction names to what was provided and return them for the
    # autocompletion. We should return the ID of the faction for simplicity. The current
    # value being entered into the autocomplete is in the interaction; see
    # https://docs.discord.com/developers/interactions/application-commands#autocomplete

    typing_value = find_list(interaction["data"]["options"], "name", "faction")

    if typing_value is None:
        return {"type": 8, "data": {"choices": []}}

    typing_value: str = str(typing_value["value"])
    pattern = str(typing_value).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    factions = Faction.select(Faction.tid, Faction.name).where(Faction.name**pattern).limit(25)

    return {
        "type": 8,
        "data": {
            "choices": [
                {
                    "name": faction.name,
                    "value": faction.tid,
                }
                for faction in factions
            ]
        },
    }

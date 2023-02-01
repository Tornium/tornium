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

from flask import render_template, request
from flask_login import current_user, login_required
from mongoengine.queryset.visitor import Q

import utils
from controllers.faction.decorators import fac_required
from models.attackmodel import AttackModel
from models.factionmodel import FactionModel
from models.usermodel import UserModel

ATTACK_RESULTS = {
    "Lost": 0,
    "Attacked": 1,
    "Mugged": 2,
    "Hospitalized": 3,
    "Stalemate": 4,
    "Escape": 5,
    "Assist": 6,
    "Special": 7,
    "Looted": 8,
    "Arrested": 9,
    "Timeout": 10,
    "Interrupted": 11,
}


@login_required
@fac_required
def attacks(*args, **kwargs):
    return render_template("faction/attacks.html")


@login_required
@fac_required
def recent_attacks(*args, **kwargs):
    start = int(request.args.get("start"))
    length = int(request.args.get("length"))

    attacks = AttackModel.objects(
        Q(attacker_faction=current_user.factiontid) | Q(defender_faction=current_user.factiontid)
    ).order_by("-timestamp")
    attacks_page = attacks[start : start + length]
    returned_attacks_data = []

    attack: AttackModel
    for attack in attacks_page:
        if attack.attacker in (0, ""):
            attacker = None
        else:
            attacker: UserModel = UserModel.objects(tid=attack.attacker).first()

        if attack.attacker_faction in (0, ""):
            attacker_faction = None
        else:
            attacker_faction: FactionModel = FactionModel.objects(tid=attack.attacker_faction).first()

        if attack.defender in (0, ""):
            defender = None
        else:
            defender: UserModel = UserModel.objects(tid=attack.defender).first()

        if attack.defender_faction in (0, ""):
            defender_faction = None
        else:
            defender_faction: FactionModel = FactionModel.objects(tid=attack.defender_faction).first()

        attack_data = {
            "attacker": "",
            "attacker_faction": "",
            "defender": "",
            "defender_faction": "",
            "respect": utils.commas(attack.respect),
            "result": next(
                (result for result, result_id in ATTACK_RESULTS.items() if result_id == attack.result), "Unknown"
            ),
            "timestamp": utils.rel_time(attack.timestamp_ended),
        }

        if attacker is not None:
            attack_data["attacker"] = f"{attacker.name} [{attacker.tid}]"
        elif attack.stealth:
            attack_data["attacker"] = "Stealthed"
        else:
            attack_data["attacker"] = f"Unknown [{attack.attacker}]"

        if attack.attacker_faction == 0:
            attack_data["attacker_faction"] = "None"
        elif attacker_faction is not None:
            attack_data["attacker_faction"] = f"{attacker_faction.name} [{attacker_faction.tid}]"
        elif attack.stealth:
            attack_data["attacker_faction"] = "Stealthed"
        else:
            attack_data["attacker_faction"] = f"Unknown [{attack.attacker_faction}]"

        if defender is not None:
            attack_data["defender"] = f"{defender.name} [{defender.tid}]"
        elif attack.stealth:
            attack_data["attacker"] = "Stealthed"
        else:
            attack_data["defender"] = f"Unknown [{attack.defender}]"

        if attack.defender_faction == 0:
            attack_data["defender_faction"] = "None"
        elif defender_faction is not None:
            attack_data["defender_faction"] = f"{defender_faction.name} [{defender_faction.tid}]"
        elif attack.stealth:
            attack_data["defender_faction"] = "Stealthed"
        else:
            attack_data["defender_faction"] = f"Unknown [{attack.defender_faction}]"

        returned_attacks_data.append(attack_data)

    return {
        "draw": request.args.get("draw"),
        "recordsTotal": AttackModel.objects().count(),
        "recordsFiltered": attacks.count(),
        "data": returned_attacks_data,
    }

# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import datetime
import math

from flask import Blueprint, request
from flask_login import login_required
from mongoengine.queryset.visitor import Q
import numpy as np

from controllers.decorators import *
from models.astatmodel import AStatModel
from models.faction import Faction
from models.factionmodel import FactionModel
from models.user import User
from models.usermodel import UserModel
import utils

mod = Blueprint('astatroutes', __name__)

# Parts of the Body
# 1 - Head
# 2 - Throat
# 3 - Heart
# 4 - Chest
# 5 - Stomach
# 6 - Left Arm
# 7 - Right Arm
# 8 - Left Hand
# 9 - Right Hand
# 10 - Groin
# 11 - Left Leg
# 12 - Right Leg
# 13 - Left Foot
# 14 - Right Foot


armor = {
    334: {
        1: 0,
        2: 0,
        3: 100,
        4: 95.73,
        5: 96.57,
        6: 36.16,
        7: 36.16,
        8: 0,
        9: 0,
        10: 11.88,
        11: 0.51,
        12: 0.51,
        13: 0,
        14: 0
    },
    642: {
        1: 85.35,
        2: 23.19,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: 0,
        12: 0,
        13: 0,
        14: 0
    },
    652: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 7.62,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 100,
        11: 100,
        12: 100,
        13: 16.28,
        14: 16.28
    },
    653: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: 7.92,
        12: 7.92,
        13: 100,
        14: 100
    },
    654: {
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0.32,
        7: 0.32,
        8: 100,
        9: 100,
        10: 0,
        11: 0,
        12: 0,
        13: 0,
        14: 0
    }
}


@mod.route('/astats')
@login_required
@pro_required
def index():
    return render_template('astats/index.html')


@mod.route('/astats/db')
@login_required
@pro_required
def stats():
    return render_template('astats/db.html')


@mod.route('/astats/dbdata')
@login_required
@pro_required
def stats_data():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    search_value = request.args.get('search[value]')

    stats = []

    if utils.get_tid(search_value):
        stat_entries = AStatModel.objects(Q(tid__startswith=utils.get_tid(search_value)) & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid)))
    else:
        stat_entries = AStatModel.objects(Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid))

    count = stat_entries.count()
    stat_entries = stat_entries[start:start+length]

    stat_entry: AStatModel
    for stat_entry in stat_entries:
        stats.append([
            stat_entry.tid,
            'N/I',
            utils.rel_time(datetime.datetime.fromtimestamp(stat_entry.timeadded))
        ])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': AStatModel.objects().count(),
        'recordsFiltered': count,
        'data': stats
    }

    return data


@mod.route('/astats/userdata')
@login_required
@pro_required
def user_data():
    tid = int(request.args.get('user'))
    stats = []
    stat_entries = AStatModel.objects(Q(tid=tid) & (Q(globalstat=True) | Q(addedid=current_user.tid) | Q(addedfactiontid=current_user.factiontid) | Q(allowedfactions=current_user.factiontid)))

    factions = {}
    users = {}

    stat_entry: AStatModel
    for stat_entry in stat_entries:
        if stat_entry.tid != tid:
            continue

        print(f'---- BEGIN Attack [{stat_entry.tid}] ----')

        user: UserModel
        faction: FactionModel

        if str(stat_entry.addedid) in users:
            user = users[str(stat_entry.addedid)]
        else:
            user = utils.first(UserModel.objects(tid=stat_entry.addedid))
            users[str(stat_entry.addedid)] = user

        if str(stat_entry.addedfactiontid) in factions:
            faction = factions[str(stat_entry.addedfactiontid)]
        else:
            faction = utils.first(FactionModel.objects(tid=stat_entry.addedfactiontid))
            factions[str(stat_entry.addedfactiontid)] = faction

        stats.append({
            'statid': stat_entry.sid,
            'tid': stat_entry.tid,
            'timeadded': stat_entry.timeadded,
            'addedid': stat_entry.addedid,
            'addedfactiontid': faction,
            'globalstat': stat_entry.globalstat
        })

        defender_base_dmg = []

        for step in stat_entry.dbs:
            # print(step['attackerItems'])

            # https://www.torn.com/forums.php#/p=threads&f=3&t=16186737&b=0&a=0&start=0&to=0
            # https://www.torn.com/forums.php#/p=threads&f=1&t=16246989&b=0&a=0&start=0&to=0
            # https://wiki.torn.com/wiki/Damage_Revamp_(2021)#Minor_Changes
            # https://www.torn.com/forums.php#/p=threads&f=61&t=16180034&b=0&a=0
            # https://www.torn.com/forums.php#/p=threads&f=61&t=16211026&b=0&a=0
            # https://www.torn.com/forums.php#/p=threads&f=61&t=16025224&b=0&a=0

            # Damage displayed value of weapon = damage multiplier
            # Base damage for headshot
            # Dmg mult for head/throat (with edu)/heart = 1
            # Dmg mult for chest/stomach/groin = 0.5714
            # Dmg mult for arm/leg = 0.2857
            # Dmg mult for hand/foot = 0.2

            # Damage value = damage pure + damage mitigated

            # Name: -sparkle - [173159]
            # Level: 82
            # results: Strength: 8, 961, 357
            # Speed: 8, 963, 117
            # Dexterity: N / A
            # Defense: 8, 958, 706
            # Total: N / A

            # ---- Armor ----
            # Body armor - slot 4
            # Helmet - slot 6
            # Pants - slot 7
            # Boots - slot 8
            # Gloves - slot 9

            if 'attacker' in step['attacking'] and step['attacking']['attacker']['result'] not in ('RELOAD', 'MISS'):
                base = 7 * math.pow(math.log10(stat_entry.attackerstr / 10), 2) + 27 * math.log10(stat_entry.attackerstr / 10) + 30
                print(f'---- Attacker ----')
                print(step['attacking'].get('attacker'))
                print(f'Base damage: {base}')

                region_multiplier = 1

                if step["attacking"]["attacker"]["result"] in ("HIT", "TEMP", "CRITICAL"):
                    if any(part in step["attacking"]["attacker"]["hitInfo"][0]["zone"].lower() for part in ('hand', 'foot')):
                        region_multiplier = 0.2
                    elif any(part in step["attacking"]["attacker"]["hitInfo"][0]["zone"].lower() for part in ('arm', 'leg')):
                        region_multiplier = 0.2857
                    elif any(part in step["attacking"]["attacker"]["hitInfo"][0]["zone"].lower() for part in ('chest', 'stomach', 'groin')):
                        region_multiplier = 0.5714
                else:
                    region_multiplier = 0

                print(f'Area multiplier: {region_multiplier}')
                print(f'Damage w/ area multiplier: {base * region_multiplier}')
                print(f'Multipliers: {(1 + step["attacking"]["attacker"]["damageDealed"]["damageModInfo"]["value"] / 100)}')
                print(f'Damage w/ multipliers: {base * region_multiplier * (1 + step["attacking"]["attacker"]["damageDealed"]["damageModInfo"]["value"] / 100)}')
                print(f'Damage dealt: {step["attacking"]["attacker"]["damageDealed"]["value"]}')
                print(f'Pure damage dealt: {step["attacking"]["attacker"]["damageDealed"]["damagePure"]}')

                # dmg_diff = step["attacking"]["attacker"]["damageDealed"]["damagePure"] - base * region_multiplier * (1 + step["attacking"]["attacker"]["damageDealed"]["damageModInfo"]["value"] / 100)
                dmg_diff = step["attacking"]["attacker"]["damageDealed"]["damageMitigated"]
                print(f'Damage difference: {dmg_diff}')

                print(f'Defense (from internal API): {step["attacking"]["attacker"]["damageDealed"]["defence"]}%')
                print(f'Remaining damage difference: {dmg_diff * 100 /(1 - step["attacking"]["attacker"]["damageDealed"]["defence"])}')

                dmg_mit = abs(dmg_diff * 100 / (step["attacking"]["attacker"]["damageDealed"]["value"]))
                print(f'Damage mitigation (%): {dmg_mit}%')

                if dmg_mit == 0:
                    def_str = 'Less than 1/64x'
                elif dmg_mit < 50:
                    def_str = math.pow(math.e, (dmg_mit - 50) * math.log2(32) / 50)
                elif dmg_mit < 100:
                    def_str = math.pow(math.e, (dmg_mit - 50) * math.log2(14) / 50)
                else:
                    def_str = 'Greater than 64x'

                print(f'Def/Str Ratio: {def_str}')
                print(f'Actual Def/Str Ratio: {8958706/stat_entry.attackerstr}')
            if 'defender' in step['attacking'] and step['attacking']['defender']['result'] not in ('RELOAD', 'MISS'):
                print(f'---- Defender ----')
                print(step['attacking'].get('defender'))
                print(f'Damage received: {step["attacking"]["defender"]["damageDealed"]["value"]}')
                print(f'Pure damage received: {step["attacking"]["defender"]["damageDealed"]["damagePure"]}')

                region_multiplier = 1

                if step["attacking"]["defender"]["result"] in ("HIT", "TEMP", "CRITICAL", "MITIGATED"):
                    if any(part in step["attacking"]["defender"]["hitInfo"][0]["zone"].lower() for part in
                           ('hand', 'foot')):
                        region_multiplier = 0.2
                    elif any(part in step["attacking"]["defender"]["hitInfo"][0]["zone"].lower() for part in
                             ('arm', 'leg')):
                        region_multiplier = 0.2857
                    elif any(part in step["attacking"]["defender"]["hitInfo"][0]["zone"].lower() for part in
                             ('chest', 'stomach', 'groin')):
                        region_multiplier = 0.5714
                else:
                    region_multiplier = 0

                base_dmg = step["attacking"]["defender"]["damageDealed"]["damagePure"] / (1 + step["attacking"]["defender"]["damageDealed"]["damageModInfo"]["value"] / 100) / region_multiplier
                defender_base_dmg.append(base_dmg)
                print(f'Area multiplier: {region_multiplier}')
                print(f'Multipliers: {(1 + step["attacking"]["defender"]["damageDealed"]["damageModInfo"]["value"] / 100)}')
                print(f'Base damage: {base_dmg}')
                print(f'Log str/10 (plus): {(-27 + math.sqrt(729 - 28 * (30 - base_dmg))) / 14}')
                strength = math.pow(10, ((-27 + math.sqrt(729 - 28 * (30 - base_dmg))) / 14) + 1)
                print(f'Strength: {utils.commas(round(strength))}')
                print('')

        print('')
        defender_base_dmg_std = np.array(defender_base_dmg).std()
        defender_base_dmg_median = np.median(np.array(defender_base_dmg))
        print(f'Defender base damage STD: {round(defender_base_dmg_std, 2)}')
        print(f'Defender base damage median: {defender_base_dmg_median}')
        normalized_defender_base_dmg = []

        for base_dmg in defender_base_dmg:
            if base_dmg >= defender_base_dmg_median - defender_base_dmg_std and base_dmg <= defender_base_dmg_median + defender_base_dmg_std:
                normalized_defender_base_dmg.append(base_dmg)

        defender_base_dmg_normalized_median = np.median(np.array(normalized_defender_base_dmg))
        print(f'Defender base damage normalized median: {defender_base_dmg_normalized_median}')
        strength = math.pow(10, ((-27 + math.sqrt(729 - 28 * (30 - defender_base_dmg_normalized_median))) / 14) + 1)
        print(f'Defender normalized median strength: {utils.commas(round(strength))}')
        print(f'---- END Attack [{stat_entry.tid}] ----')
        print('')

    user: User = User(tid=tid)

    # If user's last action was over a month ago and last refresh was over a week ago
    if utils.now() - user.last_action > 30 * 24 * 60 * 60 and utils.now() - user.last_refresh > 604800:
        user.refresh(key=current_user.key)
    elif utils.now() - user.last_action <= 30 * 24 * 60 * 60:
        user.refresh(key=current_user.key)

    if user.factiontid != 0:
        faction: Faction = Faction(tid=user.factiontid)
    else:
        faction = None

    respect = 0
    ff = 0

    return render_template('stats/statmodal.html', user=user, faction=faction, stats=stats, ff=round(ff, 2),
                           respect=round(respect, 2))


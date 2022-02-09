# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import logging
import math
import random

from honeybadger import honeybadger
import requests
from models.factiongroupmodel import FactionGroupModel

from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.usermodel import UserModel
from tasks import celery_app, discordpost, logger, tornget, torn_stats_get
import utils

logger: logging.Logger


@celery_app.task
def refresh_factions():
    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects():
        if len(faction.keys) == 0:
            continue

        try:
            faction_data = tornget(
                'faction/?selections=',
                key=random.choice(faction.keys),
                session=requests_session
            )
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        if faction_data is None:
            continue

        faction = utils.first(FactionModel.objects(tid=faction.tid))
        faction.name = faction_data['name']
        faction.respect = faction_data['respect']
        faction.capacity = faction_data['capacity']
        faction.leader = faction_data['leader']
        faction.coleader = faction_data['co-leader']
        faction.last_members = utils.now()
        faction.save()

        keys = []

        leader = utils.first(UserModel.objects(tid=faction.leader))
        coleader = utils.first(UserModel.objects(tid=faction.coleader))

        if leader is not None and leader.key != '':
            keys.append(leader.key)
        if coleader is not None and coleader.key != '':
            keys.append(coleader.key)

        if len(keys) != 0:
            try:
                user_ts_data = torn_stats_get(f'spy/faction/{faction.tid}', random.choice(keys))
            except Exception as e:
                logger.exception(e)
                return

            if not user_ts_data['status']:
                return

            for user_id, user_data in user_ts_data['faction']['members']:
                if 'spy' not in user_data:
                    continue

                user: UserModel = utils.first(UserModel.objects(tid=int(user_id)))

                if user is None:
                    continue
                elif user_data['spy']['timestamp'] <= user.battlescore_update:
                    continue

                user.battlescore = math.sqrt(user_data['spy']['strength']) + math.sqrt(user_data['spy']['defense']) + \
                                   math.sqrt(user_data['spy']['speed']) + math.sqrt(user_data['spy']['dexterity'])
                user.strength = user_data['spy']['strength']
                user.defense = user_data['spy']['defense']
                user.speed = user_data['spy']['speed']
                user.dexterity = user_data['spy']['dexterity']
                user.battlescore_update = utils.now()
                user.save()

        users = []

        for member_id, member in faction_data['members'].items():
            user = utils.first(UserModel.objects(tid=int(member_id)))
            users.append(int(member_id))

            if user is None:
                user = UserModel(
                    tid=int(member_id),
                    name=member['name'],
                    level=member['level'],
                    last_refresh=utils.now(),
                    admin=False,
                    key='',
                    battlescore=0,
                    battlescore_update=utils.now(),
                    discord_id=0,
                    servers=[],
                    factionid=faction.tid,
                    factionaa=False,
                    chain_hits=0,
                    status=member['last_action']['status'],
                    last_action=member['last_action']['timestamp']
                )
                user.save()

            user.name = member['name']
            user.level = member['level']
            user.last_refresh = utils.now()
            user.factionid = faction.tid
            user.status = member['last_action']['status']
            user.last_action = member['last_action']['timestamp']
            user.save()

        for user in UserModel.objects(factionid=faction.tid):
            if user.tid in users:
                continue

            user.factionid = 0
            user.factionaa = False
            user.save()

        if faction.chainconfig['od'] == 1:
            try:
                faction_od = tornget(
                    'faction/?selections=contributors',
                    stat='drugoverdoses',
                    key=random.choice(faction.keys),
                    session=requests_session
                )
            except Exception as e:
                logger.exception(e)
                continue

            if len(faction.chainod) > 0:
                for tid, user_od in faction_od['contributors']['drugoverdoses'].items():
                    if user_od != faction.chainod.get(tid):
                        overdosed_user = utils.first(UserModel.objects(tid=tid))
                        payload = {
                            'embeds': [
                                {
                                    'title': 'User Overdose',
                                    'description': f'User {tid if overdosed_user is None else overdosed_user.name} of '
                                                   f'faction {faction.name} has overdosed.',
                                    'timestamp': datetime.datetime.utcnow().isoformat(),
                                    'footer': {
                                        'text': utils.torn_timestamp()
                                    }
                                }
                            ]
                        }

                        try:
                            discordpost.delay(
                                f'channels/{faction.chainconfig["odchannel"]}/messages',
                                payload=payload
                            )
                        except Exception as e:
                            logger.exception(e)
                            honeybadger.notify(e)
                            continue

            faction.chainod = faction_od['contributors']['drugoverdoses']

        faction.save()


@celery_app.task
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    requests_session = requests.Session()
    statid = utils.last(StatModel.objects()).statid  # Current last stat ID

    try:
        last_timestamp = utils.first(StatModel.objects(statid=statid)).timeadded
    except AttributeError:
        last_timestamp = 0

    faction_shares = {}

    group: FactionGroupModel
    for group in FactionGroupModel.objects():
        for member in group.sharestats:
            if str(member) in faction_shares:
                faction_shares[str(member)].extend(group.members)
            else:
                faction_shares[str(member)] = group.members

    for factiontid, shares in faction_shares.items():
        faction_shares[factiontid] = list(set(shares))

    for faction in FactionModel.objects():
        if len(faction.keys) == 0:
            continue
        elif faction.config['stats'] == 0:
            continue

        try:
            faction_data = tornget('faction/?selections=basic,attacks', key=random.choice(faction.keys),
                                   session=requests_session)
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        for attack in faction_data['attakcs'].values():
            if attack['defender_faction'] == faction_data['ID']:
                continue
            elif attack['result'] in ['Assist', 'Lost', 'Stalemate', 'Escape']:
                continue
            elif attack['defender_id'] in [4, 10, 15, 17, 19, 20, 21]:  # Checks if NPC fight (and you defeated NPC)
                continue
            elif attack['modifiers']['fair_fight'] == 3:  # 3x FF can be greater than the defender battlescore indicated
                continue
            elif attack['timestamp_ended'] < last_timestamp:
                continue

            user = utils.first(UserModel.objects(tid=attack['attacker_id']))

            if user is None:
                try:
                    user_data = tornget(f'user/{attack["attacker_id"]}/?selections=profile,discord',
                                        random.choice(faction.keys),
                                        session=requests_session)

                    user = UserModel(
                        tid=attack['attacker_id'],
                        name=user_data['name'],
                        level=user_data['level'],
                        admin=False,
                        key='',
                        battlescore=0,
                        battlescore_update=utils.now(),
                        discord_id=user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0,
                        servers=[],
                        factionid=user_data['faction']['faction_id'],
                        factionaa=False,
                        last_refresh=utils.now(),
                        chain_hits=0,
                        status=user_data['last_action']['status'],
                        last_action=user_data['last_action']['timestamp']
                    )
                    user.save()
                except Exception as e:
                    logger.exception(e)
                    continue

            try:
                if user.battlescore_update - utils.now() <= 10800000:  # Three hours
                    attacker_score = user.battlescore
                else:
                    continue
            except IndexError:
                continue

            if attacker_score > 100000:
                continue

            defender_score = (attack['modifiers']['fair_fight'] - 1) * 0.375 * attacker_score

            if defender_score == 0:
                continue

            stat_faction: FactionModel = utils.first(FactionModel.objects(tid=user.factionid))

            if stat_faction is None:
                globalstat = 1
                allowed_factions = []
            else:
                globalstat = stat_faction.statconfig['global']
                allowed_factions = [stat_faction.tid]

                if str(stat_faction.tid) in faction_shares:
                    allowed_factions.extend(faction_shares[str(stat_faction.tid)])

                allowed_factions = list(set(allowed_factions))

            stat_entry = StatModel(
                statid=statid,
                tid=attack['defender_id'],
                battlescore=defender_score,
                timeadded=utils.now(),
                addedid=attack['attacker_id'],
                addedfactiontid=user.factionid,
                globalstat=globalstat,
                allowedfactions=allowed_factions
            )
            stat_entry.save()
            statid += 1

# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import math

from honeybadger import honeybadger
from models.recruitmodel import RecruitModel
from mongoengine.queryset.visitor import Q
import requests

from models.usermodel import UserModel
from tasks import celery_app, logger, tornget
import utils


@celery_app.task
def refresh_users():
    reqeusts_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(key__ne=''):
        if user.key == '':
            continue

        try:
            user_data = tornget(f'user/?selections=profile,battlestats,discord', user.key, session=reqeusts_session)
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        user.factionid = user_data['faction']['faction_id']
        user.name = user_data['name']
        user.last_refresh = utils.now()
        user.status = user_data['last_action']['status']
        user.last_action = user_data['last_action']['timestamp']
        user.level = user_data['level']
        user.discord_id = user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0
        user.strength = user_data['strength']
        user.defense = user_data['defense']
        user.speed = user_data['speed']
        user.dexterity = user_data['dexterity']

        battlescore = math.sqrt(user_data['strength']) + math.sqrt(user_data['defense']) + \
                      math.sqrt(user_data['speed']) + math.sqrt(user_data['dexterity'])
        user.battlescore = battlescore
        user.battlescore_update = utils.now()
        user.save()

        try:
            tornget(f'faction/?selections=positions', user.key, session=reqeusts_session)
        except utils.TornError as e:
            if e.code != 7:
                logger.exception(e)
                honeybadger.notify(e)
                continue
            else:
                if user.factionaa:
                    user.factionaa = False
                    user.save()
                    continue
                else:
                    logger.exception(e)
                    continue
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)

            if user.factionaa:
                user.factionaa = False
                user.save()

            continue

        user.factionaa = True
        user.save()


@celery_app.task
def mail_check():
    requests_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(Q(key__ne='') & Q(pro=1)):
        if user.key == '' or not user.pro:
            continue

        try:
            mail_data = tornget(
                f'user/?selections=messages',
                user.key,
                session=requests_session, 
                fromts=user.recruit_mail_update
            )
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        for mailid, mail in mail_data.items():
            if mail['type'] != 'User message':
                continue
            elif user.recruiter_code not in mail['title']:
                continue
            
            recruit: RecruitModel = utils.last(RecruitModel.objects(Q(tid=mail["ID"]) & Q(recruiter=user.tid)))

            if recruit is None:
                continue
            if recruit.status == 2:
                continue

            recruit.messages_received += 1
            recruit.save()

        user.recruit_mail_update = utils.now()
        user.save()

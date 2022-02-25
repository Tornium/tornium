# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import login_required
from mongoengine.queryset.visitor import Q

from controllers.faction.decorators import *
from models.recruitmodel import RecruitModel
from models.user import User
from models.usermodel import UserModel
import utils


@login_required
@aa_recruitment_required
def dashboard():
    messages_sent = 0
    members_invited = 0
    members_joined = 0
    members_retainedweek = 0
    members_retainedmonth = 0

    recruit: RecruitModel
    for recruit in RecruitModel.objects(Q(recruiter=current_user.tid) & Q(factionid=current_user.factiontid)):
        messages_sent += recruit.messages_received

        if recruit.status in (1, 2):
            members_invited += 1
        if recruit.status == 2:
            members_joined += 1

        if recruit.tif >= 7:
            members_retainedweek += 1
        if recruit.tif >= 31:
            members_retainedmonth += 1

    return render_template(
        'faction/recruitment.html',
        recruiters=recruiters,
        recruiter_code=current_user.recruiter_code,
        recruiter_sent=messages_sent,
        recruiter_invited=members_invited,
        recruiter_joined=members_joined,
        recruiter_retainedweek=members_retainedweek,
        recruiter_retainedmonth=members_retainedmonth
    )


@login_required
@aa_recruitment_required
def recruiters():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    recruiters = []

    recruiter: UserModel
    for recruiter in UserModel.objects(Q(factionid=current_user.factiontid) & Q(recruiter=True))[start:start+length]:
        messages_sent = 0
        members_invited = 0
        members_joined = 0
        members_retainedweek = 0
        members_retainedmonth = 0

        recruit: RecruitModel
        for recruit in RecruitModel.objects(Q(recruiter=recruiter.tid) & Q(factionid=current_user.factiontid)):
            messages_sent += recruit.messages_received

            if recruit.status in (1, 2):
                members_invited += 1
            if recruit.status == 2:
                members_joined += 1

            if recruit.tif >= 7:
                members_retainedweek += 1
            if recruit.tif >= 31:
                members_retainedmonth += 1
        
        recruiters.append([
            f'{recruiter.name} [{recruiter.tid}]',
            messages_sent,
            members_invited,
            members_joined,
            members_retainedweek,
            members_retainedmonth
        ])
    
    return {
        'draw': request.args.get('draw'),
        'recordsTotal': UserModel.objects(Q(factionid=current_user.factiontid) & Q(recruiter=True)).count(),
        'recordsFiltered': UserModel.objects(Q(factionid=current_user.factiontid) & Q(recruiter=True))[start:start+length].count(),
        'data': recruiters
    }


@login_required
@aa_recruitment_required
def recruits():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    recruits = []

    recruit: RecruitModel
    for recruit in RecruitModel.objects(factionid=current_user.factiontid)[start:start+length]:
        recruiter: UserModel = utils.first(UserModel.objects(tid=recruit.recruiter))
        recruit_user = User(recruit.tid).refresh(key=current_user.key)

        if recruit.status == 0:
            status = 'Not Invited'
        elif recruit.status == 1:
            status = 'Invited'
        elif recruit.status == 2:
            status = 'Joined'
        else:
            status = recruit.status
        
        recruits.append([
            recruit.uuid,
            f'{recruit_user.name} [{recruit.tid}]',
            f'{recruiter.name} [{recruiter.tid}]',
            status,
            recruit.messages_received,
            f'{recruit.tif} days'
        ])
    
    return {
        'draw': request.args.get('draw'),
        'recordsTotal': RecruitModel.objects().count(),
        'recordsFiltered': RecruitModel.objects(factionid=current_user.factiontid).count(),
        'data': recruits
    }

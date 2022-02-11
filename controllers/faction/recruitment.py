# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template, request
from flask_login import login_required
from mongoengine.queryset.visitor import Q

from controllers.faction.decorators import *
from models.recruitmodel import RecruitModel
from models.usermodel import UserModel
import utils


@login_required
@aa_recruitment_required
def dashboard():
    recruiters = []

    recruiter: UserModel
    for recruiter in UserModel.objects(Q(factionid=current_user.factiontid) & Q(recruiter=True)):
        recruiters.append({
            'name': recruiter.name,
            'tid': recruiter.tid,
            'sent': 'N/I',
            'invited': 'N/I',
            'joined': 'N/I',
            'retainedweek': 'N/I',
            'retainedmonth': 'N/I'
        })

    return render_template(
        'faction/recruitment.html',
        recruiters=recruiters,
        recruiter_code='N/I',
        recruiter_sent='N/I',
        recruiter_invited='N/I',
        recruiter_joined='N/I',
        recruiter_retainedweek='N/I',
        recruiter_retainedmonth='N/I'
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
        
        recruiters.append([
            f'{recruiter.name} [{recruiter.tid}]',
            messages_sent,
            'N/I',
            'N/I',
            'N/I',
            'N/I'
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
    for recruit in RecruitModel.objects(factionid=current_user.factiontid):
        recruiter: UserModel = utils.first(UserModel.objects(tid=recruit.recruiter))
        
        recruits.append([
            recruit.uuid,
            f'{utils.first(UserModel.objects(tid=recruit.tid)).name} [{recruit.tid}]',
            f'{recruiter.name} [{recruiter.tid}]',
            recruit.messages_received,
            recruit.tif
        ])
    
    return {
        'draw': request.args.get('draw'),
        'recordsTotal': RecruitModel.objects().count(),
        'recordsFiltered': RecruitModel.objects(factionid=current_user.factiontid).count(),
        'data': recruits
    }

# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from flask import render_template
from flask_login import login_required
from mongoengine.queryset.visitor import Q

from controllers.faction.decorators import *
from models.usermodel import UserModel


@login_required
@aa_recruitment_required
def dashboard():
    recruiters = []

    recruiter: UserModel
    for recruiter in UserModel.objects(Q(factionid=current_user.factiontid) & Q(recruiter=True)):
        recruiters.append({
            'name': recruiter.name,
            'tid': recruiter.tid,
            'status': 'N/I',
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

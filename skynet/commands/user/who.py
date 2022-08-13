# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

from models.usermodel import UserModel
import utils


def who(interaction):
    print(interaction)

    if "options" in interaction["data"]:
        member = utils.find_list(interaction["data"]["options"], "name", "member")
    else:
        if "member" in interaction:
            user: UserModel = UserModel.objects(
                discord_id=interaction["member"]["user"]["id"]
            ).first()
        else:
            user: UserModel = UserModel.objects(
                discord_id=interaction["user"]["id"]
            ).first()

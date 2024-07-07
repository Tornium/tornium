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

from flask import redirect, render_template, request
from peewee import DoesNotExist
from tornium_celery.tasks.api import discorddelete
from tornium_commons.models import Assist, AssistMessage


def assist_forward(guid: str):
    def r_0():
        return (
            render_template(
                "errors/error.html",
                title="Assist Request Already Fulfilled",
                error=f"The {mode} request on the attack has already been fulfilled.",
            ),
            400,
        )

    mode = request.args.get("mode")

    if mode not in ("smoke", "tear", "heavy"):
        return (
            render_template(
                "errors/error.html",
                title="Unknown Assist Type",
                error=f'"{mode}" is not recognized by Tornium as an acceptable assist type.',
            ),
            400,
        )

    try:
        assist: Assist = Assist.select().where(Assist.guid == guid).get()
    except DoesNotExist:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Assist ID",
                error=f"No assist could be located with ID {guid}. Please make sure that the assist request wasn't sent more than five minutes ago.",
            ),
            400,
        )

    if mode == "smoke":
        if assist.remaining_smokes <= 0:
            return r_0()

        Assist.update(remaining_smokes=Assist.remaining_smokes - 1).where(Assist.guid == guid).execute()
    elif mode == "tear":
        if assist.remaining_tears <= 0:
            return r_0()

        Assist.update(remaining_tears=Assist.remaining_tears - 1).where(Assist.guid == guid).execute()
    elif mode == "heavy":
        if assist.remaining_heavies <= 0:
            return r_0()

        Assist.update(remaining_heavies=Assist.remaining_heavies - 1).where(Assist.guid == guid).execute()
    else:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Assist Type",
                error=f'"{mode}" is not recognized by Tornium as a valid assist type.',
            ),
            400,
        )

    if assist.remaining_smokes + assist.remaining_tears + assist.remaining_heavies <= 0:
        if len(assist.sent_messages) > 0:
            message: AssistMessage
            for message in (
                AssistMessage.delete().where(AssistMessage.message_id << assist.sent_messages).returning(AssistMessage)
            ):
                discorddelete.delay(f"channels/{message.channel_id}/messages/{message.message_id}").forget()

        assist.delete_instance()

    return redirect(f"https://www.torn.com/loader2.php?sid=getInAttack&user2ID={assist.target.tid}")

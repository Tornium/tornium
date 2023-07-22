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
from redis.commands.json.path import Path
from tornium_celery.tasks.api import discordpatch
from tornium_commons import rds

_MODE_VAR_MAP = {
    "smoke": "smokes",
    "tear": "tears",
    "heavy": "heavies",
}


def assist_forward(guid: str):
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

    redis_client = rds()
    assist_data = redis_client.get(f"tornium:assists:{guid}")

    if assist_data is None:
        return (
            render_template(
                "errors/error.html",
                title="Unknown Assist ID",
                error=f"No assist could be located with ID {guid}. Please make sure that the assist request wasn't sent more than ten minutes ago.",
            ),
            400,
        )

    target_tid, user_tid, smokes, tears, heavies = [int(n) for n in assist_data.split("|")]

    if globals()[_MODE_VAR_MAP[mode]] <= 0:
        return (
            render_template(
                "errors/error.html",
                title="Assist Request Already Fulfilled",
                error=f"The {mode} request on the attack has already been fulfilled.",
            ),
            400,
        )

    globals()[_MODE_VAR_MAP[mode]] -= 1
    redis_client.set(
        f"tornium:assists:{guid}", f"{target_tid}|{user_tid}|{smokes}|{tears}|{heavies}", xx=True, keepttl=True
    )

    if smokes + tears + heavies <= 0:
        return redirect(f"https://www.torn.com/loader2.php?sid=getInAttack&user2ID={target_tid}")

    messages: set = redis_client.smembers(f"tornium:assists:{guid}:messages")

    if len(messages) == 0:
        return redirect(f"https://www.torn.com/loader2.php?sid=getInAttack&user2ID={target_tid}")

    payload = redis_client.json().get(f"tornium:assists:{guid}:payload")

    if payload is None:
        return redirect(f"https://www.torn.com/loader2.php?sid=getInAttack&user2ID={target_tid}")

    i = 0

    field: dict
    for field in payload["embeds"][0]["fields"]:
        if "Heavies" in field["name"]:
            if heavies == 0:
                payload["embeds"][0]["fields"].pop(i)
                payload["components"][0]["components"].pop(i)
            else:
                field["value"] = heavies
        elif "Tears" in field["name"]:
            if tears == 0:
                payload["embeds"][0]["fields"].pop(i)
                payload["components"][0]["components"].pop(i)
            else:
                field["value"] = tears
        elif "Smokes" in field["name"]:
            if smokes == 0:
                payload["embeds"][0]["fields"].pop(i)
                payload["components"][0]["components"].pop(i)
            else:
                field["value"] = smokes

        i += 1

    redis_client.json().set(f"tornium:assists:{guid}:payload", Path.root_path(), payload, xx=True)

    for message in messages:
        channel_id, message_id = [int(n) for n in message.split("|")]

        discordpatch.delay(f"channels/{channel_id}/messages/{message_id}", payload=payload).forget()

    return redirect(f"https://www.torn.com/loader2.php?sid=getInAttack&user2ID={target_tid}")

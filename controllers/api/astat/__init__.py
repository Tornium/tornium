# Copyright (C) tiksan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by tiksan <webmaster@deek.sh>

import json
import math

from mongoengine.queryset.visitor import Q
import numpy as np

from controllers.api.decorators import *
from models.astatmodel import AStatModel
import utils


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={"admin", "write:stats", "admin:stats"})
def attack_start(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    network_attack = json.loads(request.get_data().decode("utf-8"))

    if network_attack["DB"]["attackStatus"] != "started":
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. An illegal attack status was passed.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif (
        kwargs["user"].strength == 0
        or kwargs["user"].defense == 0
        or kwargs["user"].speed == 0
        or kwargs["user"].dexterity == 0
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The user has no battlestats stored.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif "attacking" not in network_attack["DB"]:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. No attacking key was in the DB object but the "
                    "attack has already been initially stored in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif network_attack["DB"].get("lootable"):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The attacked user is lootable and therefore assumed to "
                    "be an NPC.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    attack: AStatModel = (
        AStatModel.objects(logid=network_attack["DB"]["logID"]).order_by("-id").first()
    )

    if attack is None:
        attack = AStatModel(
            sid=AStatModel.objects().order_by("-id").first() + 1
            if AStatModel.objects.count() != 0
            else 0,
            logid=network_attack["DB"]["logID"],
            tid=network_attack["DB"]["defenderUser"]["userID"],
            timeadded=utils.now(),
            addedid=kwargs["user"].tid,
            addedfactionid=kwargs["user"].factionid,
            attackerstr=kwargs["user"].strength,
            attackerdef=kwargs["user"].defense,
            attackerspd=kwargs["user"].speed,
            attackerdex=kwargs["user"].dexterity,
        )
        attack.dbs.append(network_attack["DB"])
        attack.save()
    else:
        attack.status = network_attack["DB"]["attackStatus"]
        attack.dbs.append(network_attack["DB"])
        attack.save()

    return (
        jsonify({"code": 1, "name": "OK", "message": "Server request was successful."}),
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={"admin", "write:stats", "admin:stats"})
def attack_end(*args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'
    network_attack = json.loads(request.get_data().decode("utf-8"))

    if network_attack["DB"]["attackStatus"] != "end":
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. An illegal attack status was passed.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif (
        kwargs["user"].strength == 0
        or kwargs["user"].defense == 0
        or kwargs["user"].speed == 0
        or kwargs["user"].dexterity == 0
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The user has no battlestats stored.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    attack: AStatModel = (
        AStatModel.objects(logid=network_attack["DB"]["logID"]).order_by("-id").first()
    )

    if "attacking" not in network_attack["DB"]:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. No attacking key was in the DB object but the "
                    "attack has already been initially stored in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif attack is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The attack was not found in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    attack.status = network_attack["DB"]["attackStatus"]
    attack.dbs.append(network_attack["DB"])
    attack.save()

    return (
        jsonify({"code": 1, "name": "OK", "message": "Server request was successful."}),
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )


@key_required
@ratelimit
@pro_required
@requires_scopes(scopes={"admin", "read:stats", "admin:stats"})
def attack_log_stats(logID, *args, **kwargs):
    client = redisdb.get_redis()
    key = f'tornium:ratelimit:{kwargs["user"].tid}'

    stat_entry: AStatModel = (
        AStatModel.objects(
            Q(logid=logID)
            & (
                Q(globalstat=True)
                | Q(addedid=kwargs["user"].tid)
                | Q(addedfactiontid=kwargs["user"].factionid)
                | Q(allowedfactions=kwargs["user"].factionid)
            )
        )
        .order_by("-id")
        .first()
    )

    if stat_entry is None:
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The attack was not found in the database.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )
    elif (
        kwargs["user"].strength == 0
        or kwargs["user"].defense == 0
        or kwargs["user"].speed == 0
        or kwargs["user"].dexterity == 0
    ):
        return (
            jsonify(
                {
                    "code": 0,
                    "name": "GeneralError",
                    "message": "Server failed to fulfill the request. The user has no battlestats stored.",
                }
            ),
            400,
            {
                "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
                "X-RateLimit-Remaining": client.get(key),
                "X-RateLimit-Reset": client.ttl(key),
            },
        )

    defender_base_dmg = []

    for step in stat_entry.dbs:
        if "attacker" in step["attacking"] and step["attacking"]["attacker"][
            "result"
        ] not in ("RELOAD", "MISS", "INEFFECTIVE"):
            base = (
                7 * math.pow(math.log10(stat_entry.attackerstr / 10), 2)
                + 27 * math.log10(stat_entry.attackerstr / 10)
                + 30
            )
            print(f"---- Attacker ----")
            print(step["attacking"].get("attacker"))
            print(f"Base damage: {base}")

            region_multiplier = 1

            if step["attacking"]["attacker"]["result"] in (
                "HIT",
                "TEMP",
                "CRITICAL",
                "WON",
            ):
                if any(
                    part in step["attacking"]["attacker"]["hitInfo"][0]["zone"].lower()
                    for part in ("hand", "foot")
                ):
                    region_multiplier = 0.2
                elif any(
                    part in step["attacking"]["attacker"]["hitInfo"][0]["zone"].lower()
                    for part in ("arm", "leg")
                ):
                    region_multiplier = 0.2857
                elif any(
                    part in step["attacking"]["attacker"]["hitInfo"][0]["zone"].lower()
                    for part in ("chest", "stomach", "groin")
                ):
                    region_multiplier = 0.5714
            else:
                region_multiplier = 0

            print(f"Area multiplier: {region_multiplier}")
            print(f"Damage w/ area multiplier: {base * region_multiplier}")
            print(
                f'Multipliers: {(1 + step["attacking"]["attacker"]["damageDealed"]["damageModInfo"]["value"] / 100)}'
            )
            print(
                f'Damage w/ multipliers: {base * region_multiplier * (1 + step["attacking"]["attacker"]["damageDealed"]["damageModInfo"]["value"] / 100)}'
            )
            print(
                f'Damage dealt: {step["attacking"]["attacker"]["damageDealed"]["value"]}'
            )
            print(
                f'Pure damage dealt: {step["attacking"]["attacker"]["damageDealed"]["damagePure"]}'
            )

            dmg_mit = step["attacking"]["attacker"]["damageDealed"]["defence"]
            print(f"Damage mitigation (%): {dmg_mit}%")

            if dmg_mit == 0:
                def_str = -2
            elif dmg_mit < 50:
                def_str = math.pow(math.e, (dmg_mit - 50) * math.log2(32) / 50)
            elif dmg_mit < 100:
                def_str = math.pow(math.e, (dmg_mit - 50) * math.log2(14) / 50)
            else:
                def_str = -1

            print(f"Def/Str Ratio: {def_str}")

            if def_str == -2:
                print(
                    f"Estimated attacker defense: less than or equal to {utils.commas(int(stat_entry.attackerstr / 64))}"
                )
            elif def_str == -1:
                print(
                    f"Estimated attacker defense: greater than or equal to {utils.commas(int(stat_entry.attackerstr * 64))}"
                )
            else:
                defender_defense = def_str * stat_entry.attackerstr
                print(
                    f"Estimated attacker defense: {utils.commas(int(defender_defense))}"
                )
        if "defender" in step["attacking"] and step["attacking"]["defender"][
            "result"
        ] not in ("RELOAD", "MISS", "INEFFECTIVE"):
            print(f"---- Defender ----")
            print(step["attacking"].get("defender"))
            print(
                f'Damage received: {step["attacking"]["defender"]["damageDealed"]["value"]}'
            )
            print(
                f'Pure damage received: {step["attacking"]["defender"]["damageDealed"]["damagePure"]}'
            )

            region_multiplier = 1

            if step["attacking"]["defender"]["result"] in (
                "HIT",
                "TEMP",
                "CRITICAL",
                "MITIGATED",
                "WON",
            ):
                if any(
                    part in step["attacking"]["defender"]["hitInfo"][0]["zone"].lower()
                    for part in ("hand", "foot")
                ):
                    region_multiplier = 0.2
                elif any(
                    part in step["attacking"]["defender"]["hitInfo"][0]["zone"].lower()
                    for part in ("arm", "leg")
                ):
                    region_multiplier = 0.2857
                elif any(
                    part in step["attacking"]["defender"]["hitInfo"][0]["zone"].lower()
                    for part in ("chest", "stomach", "groin")
                ):
                    region_multiplier = 0.5714

                base_dmg = (
                    step["attacking"]["defender"]["damageDealed"]["damagePure"]
                    / (
                        1
                        + step["attacking"]["defender"]["damageDealed"][
                            "damageModInfo"
                        ]["value"]
                        / 100
                    )
                    / region_multiplier
                )
                defender_base_dmg.append(base_dmg)
                print(f"Area multiplier: {region_multiplier}")
                print(
                    f'Multipliers: {(1 + step["attacking"]["defender"]["damageDealed"]["damageModInfo"]["value"] / 100)}'
                )
                print(f"Base damage: {base_dmg}")
                print(
                    f"Log str/10 (plus): {(-27 + math.sqrt(729 - 28 * (30 - base_dmg))) / 14}"
                )
                strength = math.pow(
                    10, ((-27 + math.sqrt(729 - 28 * (30 - base_dmg))) / 14) + 1
                )
                print(f"Strength: {utils.commas(round(strength))}")
                print("")

    print("")
    defender_base_dmg_std = np.array(defender_base_dmg).std()
    defender_base_dmg_median = np.median(np.array(defender_base_dmg))
    print(f"Defender base damage STD: {round(defender_base_dmg_std, 2)}")
    print(f"Defender base damage median: {defender_base_dmg_median}")
    normalized_defender_base_dmg = []

    for base_dmg in defender_base_dmg:
        if (
            base_dmg >= defender_base_dmg_median - defender_base_dmg_std
            and base_dmg <= defender_base_dmg_median + defender_base_dmg_std
        ):
            normalized_defender_base_dmg.append(base_dmg)

    defender_base_dmg_normalized_median = np.median(
        np.array(normalized_defender_base_dmg)
    )
    print(
        f"Defender base damage normalized median: {defender_base_dmg_normalized_median}"
    )
    strength = math.pow(
        10,
        ((-27 + math.sqrt(729 - 28 * (30 - defender_base_dmg_normalized_median))) / 14)
        + 1,
    )
    print(f"Number of actions: {len(defender_base_dmg)}")
    print(f"Number of normalized actions: {len(normalized_defender_base_dmg)}")
    print(f"Defender normalized median strength: {utils.commas(round(strength))}")
    print(f"---- END Attack [{stat_entry.tid}] ----")
    print("")

    return (
        jsonify(
            {
                "code": 1,
                "name": "OK",
                "message": "Server request was successful.",
                "strength": {
                    "median": strength,
                    "actions": len(defender_base_dmg),
                    "normalized_actions": len(normalized_defender_base_dmg),
                },
            }
        ),
        200,
        {
            "X-RateLimit-Limit": 250 if kwargs["user"].pro else 150,
            "X-RateLimit-Remaining": client.get(key),
            "X-RateLimit-Reset": client.ttl(key),
        },
    )

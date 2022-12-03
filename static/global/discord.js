/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const guildid = document.currentScript.getAttribute("data-guildid");
const key = document.currentScript.getAttribute("data-key");

if(guildid !== null && key !== null) {
    setDiscordSelectors();
}

function setDiscordSelectors() {
    let discordRoles = null;
    let discordChannels = null;

    let rolesRequest = new XMLHttpRequest();
    let channelsRequest = new XMLHttpRequest();

    rolesRequest.onload = function() {
        let response = rolesRequest.response;

        if("code" in response) {
            generateToast("Discord Roles Not Located", response["message"]);
            return;
        }

        discordRoles = response["roles"];

        $.each(response["roles"], function(role_id, role) {
            $(".discord-role-selector").append($("<option>", {
                "value": role.id,
                "text": role.name
            }));
        });
    }
    rolesRequest.responseType = "json";
    rolesRequest.open("GET", `/api/bot/server/${guildid}/roles`)
    rolesRequest.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    rolesRequest.setRequestHeader("Content-Type", "application/json");

    if($(".discord-role-selector").length !== 0) {
        rolesRequest.send();
    }

    channelsRequest.onload = function() {
        let response = channelsRequest.response;

        if("code" in response) {
            generateToast("Discord Channels Not Located", response["message"]);
            return;
        }

        discordChannels = response["channels"];

        $.each(response["channels"], function(category_id, category) {
            $(".discord-channel-selector").append($("<optgroup>", {
                "label": category.name,
                "data-category-id": category_id
            }));

            $.each(category["channels"], function(channel_id, channel) {
                $(`optgroup[data-category-id="${category_id}"]`).append($("<option>", {
                    "value": channel.id,
                    "text": `#${channel.name}`
                }))
            })
        });
    }
    channelsRequest.responseType = "json";
    channelsRequest.open("GET", `/api/bot/server/${guildid}/channels`)
    channelsRequest.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    channelsRequest.setRequestHeader("Content-Type", "application/json");

    if($(".discord-channel-selector").length !== 0) {
        channelsRequest.send();
    }
}
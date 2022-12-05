/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const guildid = document.currentScript.getAttribute("data-guildid");
const key = document.currentScript.getAttribute("data-key");

var discordRoles = null;
var discordChannels = null;

let rolesRequest = obj => {
    return new Promise((resolve, reject) => {
        let xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;
    
            if("code" in response) {
                generateToast("Discord Roles Not Located", response["message"]);
                reject();
                return;
            }
    
            discordRoles = response["roles"];
    
            $.each(response["roles"], function(role_id, role) {
                $(".discord-role-selector").append($("<option>", {
                    "value": role.id,
                    "text": role.name
                }));
            });
    
            // $(".discord-role-selector").selectpicker();
            resolve();
        }
        xhttp.responseType = "json";
        xhttp.open("GET", `/api/bot/server/${guildid}/roles`)
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");

        if(guildid !== null && key !== null && $(".discord-role-selector").length !== 0) {
            xhttp.send();
        }
    })
}

let channelsRequest = obj => {
    return new Promise((resolve, reject) => {
        let xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;
    
            if("code" in response) {
                generateToast("Discord Channels Not Located", response["message"]);
                reject();
                return;
            }
    
            discordChannels = response["channels"];
    
            $.each(response["channels"], function(category_id, category) {
                $(".discord-channel-selector").append($("<optgroup>", {
                    "label": category.name,
                    "data-category-id": category["id"]
                }));
    
                $.each(category["channels"], function(channel_id, channel) {
                    $(`optgroup[data-category-id="${category["id"]}"]`).append($("<option>", {
                        "value": channel.id,
                        "text": `#${channel.name}`
                    }))
                })
            });
    
            // $(".discord-channel-selector").selectpicker();
            resolve();
        }
        xhttp.responseType = "json";
        xhttp.open("GET", `/api/bot/server/${guildid}/channels`)
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
    
        if(guildid !== null && key !== null && $(".discord-channel-selector").length !== 0) {
            xhttp.send();
        }
    })
}
/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const guildid = document.currentScript.getAttribute("guildid");
const key = document.currentScript.getAttribute("data-key");

$(document).ready(function() {
    let chainConfig = null;
    let channels = null;

    let xhttp = new XMLHttpRequest();

    xhttp.onload = function() {
        let response = xhttp.response;

        if("code" in response) {
            generateToast("Chain OD Config Not Located", response["message"]);
            throw new Error("Chain OD config error");
        }

        chainConfig = response;

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Discord Channels Not Located", response["message"]);
            } else {
                channels = response["channels"];

                $.each(response["channels"], function (category_id, category) {
                    let optgroup = $("<optgroup>", {
                        "label": category["name"]
                    });

                    $("#od-channel").append(optgroup);

                    $.each(category["channels"], function(channel_id, channel) {
                        if(chainConfig["od"]["channel"] === parseInt(channel.id)) {
                            optgroup.append($(`<option value="${channel.id}" selected>#${channel.name}</option>`));
                        } else {
                            optgroup.append($(`<option value="${channel.id}">#${channel.name}</option>`));
                        }
                    });
                });
            }
        }

        xhttp.open("GET", `/api/bot/server/${guildid}/channels`);
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    }

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/faction/chain`);
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $("#od-channel").on("change", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Log Channel Failed", response["message"]);
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/chain/od");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "channel": this.options[this.selectedIndex].value
        }));
    })
})
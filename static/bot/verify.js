/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const guildid = document.currentScript.getAttribute('data-guildid');
const key = document.currentScript.getAttribute('data-key');

$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true
    });

    $("#verification-config-enable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Verification Enable Failed", `The Tornium API server has responded with \"${response["message"]}\".`)
            } else {
                generateToast("Verification Enable Successful", "The Tornium API server has been successfully enabled.")
                $("#verification-config-enable").prop("disabled", true)
                $("#verification-config-disable").prop("disabled", false)
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid
        }));
    });

    $("#verification-config-disable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Verification Enable Failed", `The Tornium API server has responded with \"${response["message"]}\".`)
            } else {
                generateToast("Verification Enable Successful", "The Tornium API server has been successfully enabled.")
                $("#verification-config-enable").prop("disabled", false)
                $("#verification-config-disable").prop("disabled", true)
            }
        }

        xhttp.responseType = "json";
        xhttp.open("DELETE", "/api/bot/verify");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid
        }));
    });

    $('#faction-verification-input').on('keypress', function(e) {
        if(e.which !== 13) {
            return;
        }

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Faction Input Failed", `The Tornium API server has responded with \"${response["message"]}\".`);
            } else {
                generateToast("Faction Input Successful");
                window.location.reload(); // TODO: Replace with dynamically adding code
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify/faction");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factiontid": $("#faction-verification-input").val()
        }));
    });

    $("#verification-log-channel").on('change', function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Log Channel Failed", `The Tornium API server has responded with \"${response["message"]}\".`);
            } else {
                generateToast("Log Channel Successful");
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify/log");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "channel": this.options[this.selectedIndex].value
        }));
    });

    $("#verification-welcome-channel").on('change', function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Welcome Channel Failed", `The Tornium API server has responded with \"${response["message"]}\".`);
            } else {
                generateToast("Welcome Channel Successful");
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify/welcome");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "channel": this.options[this.selectedIndex].value
        }));
    });

    $(".verification-faction-disable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {

            } else {
                generateToast("Faction Disabled Successfully");
            }
        }

        xhttp.responseType = "json";
        xhttp.open("DELETE", "/api/bot/verify/faction");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factionid": this.getAttribute("data-faction")
        }));
    });

    $(".verification-faction-enable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {

            } else {
                generateToast("Faction Enabled Successfully");
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify/faction");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factionid": this.getAttribute("data-faction")
        }));
    });
})

/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const key = document.currentScript.getAttribute('data-key');
const tid = document.currentScript.getAttribute('data-tid');

$(document).ready(function() {
    $("#name-form").submit(function(e) {
        e.preventDefault();

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                generateToast("Request Successfully Sent", `The request to the Tornium API server has been successfully submitted to the server.`);
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/group");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'groupid': tid,
            'action': 'name',
            'value': $("#groupname").val()
        }));
    });

    $(".remove").on("click", function(e) {
        const factiontid = Number(e.target.id.split('-')[1]);

        if(!window.confirm("Are you sure?")) {
            return
        }

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                generateToast("Request Successfully Sent", `The request to the Tornium API server has been successfully submitted to the server.`);
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/group");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'groupid': tid,
            'action': 'remove',
            'value': factiontid
        }));
    });

    $("#refresh-invite").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                generateToast("Request Successfully Sent", `The request to the Tornium API server has been successfully submitted to the server.`);
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/group");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'groupid': tid,
            'action': 'invite'
        }));
    });

    $("#delete-group").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response && response["code"] !== 1) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                generateToast("Request Successfully Sent", `The request to the Tornium API server has been successfully submitted to the server.`);
                window.location = "/faction/groups";
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/group");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'groupid': tid,
            'action': 'delete'
        }));
    });

    $("#share-statdb").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response && response["code"] !== 1) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                generateToast("Request Successfully Sent", `The request to the Tornium API server has been successfully submitted to the server.`);
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/group");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'groupid': tid,
            'action': 'share-statdb',
            'value': this.checked
        }));
    });
});

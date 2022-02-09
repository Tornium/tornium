/* This file is part of Tornium.

Tornium is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Tornium is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Tornium.  If not, see <https://www.gnu.org/licenses/>. */

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

    $("#refresh-invite").on("click", function(e) {
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

    $("#delete-group").on("click", function(e) {
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

    $("#share-statdb").on("click", function(e) {
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

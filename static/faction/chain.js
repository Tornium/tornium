/* Copyright (C) 2021-2023 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

const guildid = document.currentScript.getAttribute("data-guildid");

$(document).ready(function () {
    let chainConfig = null;
    let channels = null;

    let xhttp = new XMLHttpRequest();

    xhttp.onload = function () {
        let response = xhttp.response;

        if ("code" in response) {
            generateToast("Chain OD Config Not Located", response["message"]);
            throw new Error("Chain OD config error");
        }

        chainConfig = response;

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast(
                    "Discord Channels Not Located",
                    response["message"]
                );
            } else {
                channels = response["channels"];

                $.each(response["channels"], function (category_id, category) {
                    let optgroup = $("<optgroup>", {
                        label: category["name"],
                    });

                    $("#od-channel").append(optgroup);

                    $.each(
                        category["channels"],
                        function (channel_id, channel) {
                            if (
                                chainConfig["od"]["channel"] ===
                                parseInt(channel.id)
                            ) {
                                optgroup.append(
                                    $(
                                        `<option value="${channel.id}" selected>#${channel.name}</option>`
                                    )
                                );
                            } else {
                                optgroup.append(
                                    $(
                                        `<option value="${channel.id}">#${channel.name}</option>`
                                    )
                                );
                            }
                        }
                    );
                });

                $(".discord-channel-selector").selectpicker();
            }
        };

        xhttp.open("GET", `/api/bot/server/${guildid}/channels`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    };

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/faction/chain`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $("#od-channel").on("change", function () {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Log Channel Failed", response["message"]);
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/chain/od/channel");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                channel: this.options[this.selectedIndex].value,
            })
        );
    });
});

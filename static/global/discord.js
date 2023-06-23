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

var discordRoles = null;
var discordChannels = null;
var serverConfig = null;

let rolesRequest = (obj) => {
    var localRoles = JSON.parse(localStorage.getItem(`roles:${guildid}`));

    if (
        localRoles &&
        Math.floor(Date.now() / 1000) - localRoles.timestamp < 60
    ) {
        return new Promise((resolve, reject) => {
            discordRoles = localRoles.roles;

            $.each(discordRoles, function (role_id, role) {
                $(".discord-role-selector").append(
                    $("<option>", {
                        value: role.id,
                        text: role.name,
                    })
                );
            });

            resolve();
        });
    } else {
        return new Promise((resolve, reject) => {
            let xhttp = new XMLHttpRequest();

            xhttp.onload = function () {
                let response = xhttp.response;

                if ("code" in response) {
                    generateToast(
                        "Discord Roles Not Located",
                        response["message"]
                    );
                    reject();
                    return;
                }

                discordRoles = response["roles"];

                $.each(response["roles"], function (role_id, role) {
                    $(".discord-role-selector").append(
                        $("<option>", {
                            value: role.id,
                            text: role.name,
                        })
                    );
                });

                localStorage.setItem(
                    `roles:${guildid}`,
                    JSON.stringify({
                        timestamp: Math.floor(Date.now() / 1000),
                        roles: discordRoles,
                    })
                );
                resolve();
            };
            xhttp.responseType = "json";
            xhttp.open("GET", `/api/bot/server/${guildid}/roles`);
            xhttp.setRequestHeader("Content-Type", "application/json");

            if (guildid !== null && $(".discord-role-selector").length !== 0) {
                xhttp.send();
            } else {
                reject();
            }
        });
    }
};

let channelsRequest = (obj) => {
    var localChannels = JSON.parse(localStorage.getItem(`channels:${guildid}`));

    if (
        localChannels &&
        Math.floor(Date.now() / 1000) - localChannels.timestamp < 60
    ) {
        return new Promise((resolve, reject) => {
            discordChannels = localChannels.roles;

            $.each(discordChannels, function (category_id, category) {
                $(".discord-channel-selector").append(
                    $("<optgroup>", {
                        label: category.name,
                        "data-category-id": category["id"],
                    })
                );

                $.each(category["channels"], function (channel_id, channel) {
                    $(`optgroup[data-category-id="${category["id"]}"]`).append(
                        $("<option>", {
                            value: channel.id,
                            text: `#${channel.name}`,
                        })
                    );
                });
            });

            resolve();
        });
    } else {
        return new Promise((resolve, reject) => {
            let xhttp = new XMLHttpRequest();

            xhttp.onload = function () {
                let response = xhttp.response;

                if ("code" in response) {
                    generateToast(
                        "Discord Channels Not Located",
                        response["message"]
                    );
                    reject();
                    return;
                }

                discordChannels = response["channels"];

                $.each(response["channels"], function (category_id, category) {
                    $(".discord-channel-selector").append(
                        $("<optgroup>", {
                            label: category.name,
                            "data-category-id": category["id"],
                        })
                    );

                    $.each(
                        category["channels"],
                        function (channel_id, channel) {
                            $(
                                `optgroup[data-category-id="${category["id"]}"]`
                            ).append(
                                $("<option>", {
                                    value: channel.id,
                                    text: `#${channel.name}`,
                                })
                            );
                        }
                    );
                });

                localStorage.setItem(
                    `channels:${guildid}`,
                    JSON.stringify({
                        timestamp: Math.floor(Date.now() / 1000),
                        channels: discordChannels,
                    })
                );
                resolve();
            };
            xhttp.responseType = "json";
            xhttp.open("GET", `/api/bot/server/${guildid}/channels`);
            xhttp.setRequestHeader("Content-Type", "application/json");

            if (
                guildid !== null &&
                $(".discord-channel-selector").length !== 0
            ) {
                xhttp.send();
            } else {
                reject();
            }
        });
    }
};

let configRequest = (obj) => {
    return new Promise((resolve, reject) => {
        if (serverConfig !== null) {
            resolve();
        } else {
            let xhttp = new XMLHttpRequest();

            xhttp.onload = function () {
                let response = xhttp.response;

                if ("code" in response) {
                    generateToast(
                        "Discord Config Not Located",
                        response["message"]
                    );
                    reject();
                    throw new Error("Config error");
                }

                serverConfig = xhttp.response;
                resolve();
            };

            xhttp.responseType = "json";
            xhttp.open("GET", `/api/bot/server/${guildid}`);
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send();
        }
    });
};

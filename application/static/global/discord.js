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

function createRoles() {
    $.each(discordRoles, function (role_id, role) {
        $(".discord-role-selector").append(
            $("<option>", {
                value: role.id,
                text: role.name,
            }),
        );
    });
}

const rolesRequest = (obj) => {
    var localRoles = JSON.parse(localStorage.getItem(`roles:${guildid}`));

    if (localRoles && Math.floor(Date.now() / 1000) - localRoles.timestamp < 60) {
        return new Promise((resolve, reject) => {
            discordRoles = localRoles.roles;
            createRoles();
            resolve();
        });
    }

    return new Promise((resolve, reject) => {
        if (guildid === null) {
            reject();
        }

        tfetch("GET", `bot/server/${guildid}/roles`, { errorTitle: "Failed to Load Server's Discord Roles" }).then(
            (response) => {
                discordRoles = response.roles;
                createRoles();

                localStorage.setItem(
                    `roles:${guildid}`,
                    JSON.stringify({
                        timestamp: Math.floor(Date.now() / 1000),
                        roles: discordRoles,
                    }),
                );
                resolve();
            },
        );
    });
};

function createChannels() {
    $.each(discordChannels, function (category_id, category) {
        $(".discord-channel-selector").append(
            $("<optgroup>", {
                label: category.name == "?" ? "No category" : category.name,
                "data-category-id": category_id,
            }),
        );

        $.each(category["channels"], function (channel_id, channel) {
            let parent = $(`optgroup[data-category-id="${category["id"]}"]`);
            parent.append(
                $("<option>", {
                    value: channel.id,
                    text: `#${channel.name}`,
                }),
            );

            if ("threads" in channel) {
                $.each(channel.threads, function (thread_id, thread) {
                    parent.append(
                        $("<option>", {
                            value: thread.id,
                            text: `#${channel.name} -> ${thread.name}`,
                        }),
                    );
                });
            }
        });
    });
}

const channelsRequest = (obj) => {
    var localChannels = JSON.parse(localStorage.getItem(`channels:${guildid}`));

    if (localChannels && Math.floor(Date.now() / 1000) - localChannels.timestamp < 60) {
        return new Promise((resolve, reject) => {
            discordChannels = localChannels.channels;
            createChannels();
            resolve();
        });
    }

    return new Promise((resolve, reject) => {
        if (guildid === null) {
            reject();
        }

        tfetch("GET", `bot/server/${guildid}/channels`, {
            errorTitle: "Failed to Load Server's Discord Channels",
        }).then((response) => {
            discordChannels = response.channels;
            createChannels();

            localStorage.setItem(
                `channels:${guildid}`,
                JSON.stringify({
                    timestamp: Math.floor(Date.now() / 1000),
                    channels: discordChannels,
                }),
            );
            resolve();
        });
    });
};

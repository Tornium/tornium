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

$(document).ready(function () {
    serverConfigPromise = tfetch("GET", `bot/server/${guildid}`, { errorTitle: "Server Config Failed to Load" });
    channelsPromise = channelsRequest();
    rolesPromise = rolesRequest();

    Promise.all([serverConfigPromise, channelsPromise])
        .then((configs) => {
            let serverConfig,
                channels = configs;
            let assistsChannel = $(`#assist-channel option[value="${serverConfig["assists"]["channel"]}"]`);

            if (assistsChannel.length !== 0) {
                assistsChannel.attr("selected", "");
            }

            let stockFeedChannel = $(`#feed-channel option[value="${serverConfig["stocks"]["channel"]}"]`);

            if (stockFeedChannel.length !== 0) {
                stockFeedChannel.attr("selected", "");
            }

            $.each(serverConfig["stocks"], function (configKey, configValue) {
                if (configKey === "percent_change" && configValue) {
                    $("#percent-change-switch").attr("checked", "");
                    $("#percent-change-enabled").text("Enabled");
                } else if (configKey === "cap_change" && configValue) {
                    $("#cap-change-switch").attr("checked", "");
                    $("#cap-change-enabled").text("Enabled");
                } else if (configKey === "new_day_price" && configValue) {
                    $("#new-day-price-switch").attr("checked", "");
                    $("#new-day-price-enabled").text("Enabled");
                } else if (configKey === "min_price" && configValue) {
                    $("#min-price-switch").attr("checked", "");
                    $("#min-price-enabled").text("Enabled");
                } else if (configKey === "max_price" && configValue) {
                    $("#max-price-switch").attr("checked", "");
                    $("#max-price-enabled").text("Enabled");
                }
            });

            $.each(serverConfig["retals"], function (factionid, factionConfig) {
                let option = $(
                    `.faction-retal-channel[data-faction="${factionid}"] option[value="${factionConfig.channel}"]`
                );

                if (option.length !== 1) {
                    return;
                }

                option.attr("selected", "");
            });

            $.each(serverConfig["banking"], function (factionid, factionConfig) {
                let option = $(
                    `.faction-banking-channel[data-faction="${factionid}"] option[value="${factionConfig.channel}"]`
                );

                if (option.length !== 1) {
                    return;
                }

                option.attr("selected", "");
            });
        })
        .finally(() => {
            $(".discord-channel-selector").selectpicker();
        });

    Promise.all([serverConfigPromise, rolesPromise])
        .then((configs) => {
            let serverConfig,
                roles = configs;

            $.each(serverConfig["retals"], function (factionid, factionConfig) {
                $.each(factionConfig["roles"], function (index, role) {
                    let option = $(`.faction-retal-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if (option.length !== 1) {
                        return;
                    }

                    option.attr("selected", "");
                });
            });

            $.each(serverConfig["banking"], function (factionid, factionConfig) {
                $.each(factionConfig["roles"], function (index, role) {
                    let option = $(`.faction-banking-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if (option.length !== 1) {
                        return;
                    }

                    option.attr("selected", "");
                });
            });

            $.each(serverConfig["assists"]["roles"], function (role_type, roles) {
                $.each(roles, function (index, role) {
                    let option = $(`#assist-${role_type}-roles option[value="${role}"]`);

                    if (option.length !== 1) {
                        return;
                    }

                    option.attr("selected", "");
                });
            });
        })
        .finally(() => {
            $(".discord-role-selector").selectpicker();
        });

    $('[data-bs-toggle="tooltip"]').tooltip({
        container: ".list-group",
    });

    function addFaction() {
        tfetch("POST", `bot/${guildid}/faction`, {
            body: { factiontid: $("#faction-id-input").val() },
            errorTitle: "Faction Add Failed",
        }).then(() => {
            window.location.reload();
        });
    }

    $("#faction-id-input").on("keypress", function (e) {
        if (e.which == 13) {
            addFaction();
        }
    });
    $("#faction-id-submit").on("click", addFaction);

    $(".remove-faction").on("click", function () {
        tfetch("DELETE", `bot/${guildid}/faction`, {
            body: { factiontid: this.getAttribute("data-factiontid") },
            errorTitle: "Faction Remove Failed",
        }).then(() => {
            window.location.reload();
        });
    });

    $("#assist-channel").on("change", function () {
        tfetch("POST", `bot/${guildid}/assists/channel`, {
            body: { channel: this.options[this.selectedIndex].value },
            errorTitle: "Assists Channel Set Failed",
        }).then(() => {});
    });

    function addAssistsFaction() {
        const id = $("#assist-faction-id").val();
        const xhttp = new XMLHttpRequest();
        // TODO: Migrate this to the API

        xhttp.onload = function () {
            window.location.reload();
        };

        xhttp.open("POST", `/bot/assists/${guildid}/update?action=faction&value=${id}`);
        xhttp.send();
    }

    $("#assist-faction-id").on("keypress", function (e) {
        if (e.which === 13) {
            addAssistsFaction();
        }
    });
    $("#assist-faction-submit").on("click", addAssistsFaction);

    $(".assist-role-selector").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        const xhttp = new XMLHttpRequest();
        tfetch("POST", `bot/${guildid}/assists/roles/${$(this).attr("id").split("-")[1]}`, {
            body: { roles: selectedRoles },
            errorTitle: "Assist Role Add Failed",
        }).then((response) => {
            generateToast("Role Add Successful");
        });
    });

    $(".faction-retal-channel").on("change", function () {
        tfetch("POST", "bot/retal/faction/channel", {
            body: {
                guildid: guildid,
                factiontid: this.getAttribute("data-faction"),
                channel: this.options[this.selectedIndex].value,
            },
            errorTitle: "Retal Channel Set Failed",
        }).then((response) => {
            generateToast("Retal Channel Set Successful");
        });
    });

    $(".faction-retal-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", "bot/retal/faction/roles", {
            body: { guildid: guildid, factiontid: this.getAttribute("data-faction"), roles: selectedRoles },
            errorTitle: "Retal Roles Add Failed",
        }).then((response) => {
            generateToast("Retal Role Add Successful");
        });
    });

    $(".faction-banking-channel").on("change", function () {
        tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-faction")}/banking`, {
            body: { channel: this.options[this.selectedIndex].value },
            errorTitle: "Banking Channel Set Failed",
        }).then((response) => {
            generateToast("Banking Channel Set Successful");
        });
    });

    $(".faction-banking-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        const xhttp = new XMLHttpRequest();
        tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-faction")}/banking`, {
            body: { roles: selectedRoles },
            errorTitle: "Banking Roles Add Failed",
        }).then((response) => {
            generateToast("Banking Roles Set Successful");
        });
    });
});

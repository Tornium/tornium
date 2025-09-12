/* Copyright (C) 2021-2025 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

function setOverdoseChannel(event) {
    const channelID = this.value == "0" ? null : this.value;
    const factionID = this.getAttribute("data-faction");

    tfetch("POST", `bot/${guildid}/faction/${factionID}/overdose`, {
        body: { channel: this.options[this.selectedIndex].value },
        errorTitle: "Overdose Channel Set Failed",
    }).then(() => {
        generateToast(
            "Overdose Channel Set Successful",
            "The channel for overdose notifications has been successfully set.",
        );
    });
}

ready(() => {
    let serverConfigPromise = tfetch("GET", `bot/server/${guildid}`, { errorTitle: "Server Config Failed to Load" });
    let channelsPromise = channelsRequest();
    let rolesPromise = rolesRequest();

    serverConfigPromise.then((config) => {
        $.each(config.attacks, function (factionid, factionConfig) {
            let option = $(
                `.faction-bonus-length[data-faction="${factionid}"] option[value="${factionConfig.chain_bonus.length}"]`,
            );
            if (option.length === 1) {
                option.attr("selected", "");

                if (factionConfig.chain_bonus.length != 100) {
                    $(`.faction-bonus-length[data-faction="${factionid}"] option[value="100"]`).removeAttr("selected");
                }
            }
        });

        document.querySelectorAll(".automatic-tom-select").forEach((element) => {
            new TomSelect(element, {
                create: false,
            });
        });
    });

    Promise.all([serverConfigPromise, channelsPromise])
        .then((configs) => {
            let serverConfig = configs[0];
            let channels = configs[1];

            $.each(serverConfig["attacks"], function (factionid, factionConfig) {
                let option = $(
                    `.faction-retal-channel[data-faction="${factionid}"] option[value="${factionConfig.retal.channel}"]`,
                );
                if (option.length === 1) {
                    option.attr("selected", "");
                }

                option = $(
                    `.faction-bonus-channel[data-faction="${factionid}"] option[value="${factionConfig.chain_bonus.channel}"]`,
                );
                if (option.length === 1) {
                    option.attr("selected", "");
                }

                option = $(
                    `.faction-alert-channel[data-faction="${factionid}"] option[value="${factionConfig.chain_alert.channel}"]`,
                );
                if (option.length === 1) {
                    option.attr("selected", "");
                }
            });

            $.each(serverConfig["banking"], function (factionid, factionConfig) {
                let option = $(
                    `.faction-banking-channel[data-faction="${factionid}"] option[value="${factionConfig.channel}"]`,
                );

                if (option.length !== 1) {
                    return;
                }

                option.attr("selected", "");
            });

            $.each(serverConfig.overdose, (factionID, overdoseChannel) => {
                let option = $(
                    `.faction-overdose-channel[data-faction="${factionID}"] option[value="${overdoseChannel}"]`,
                );

                if (option.length !== 1) {
                    return;
                }

                option.attr("selected", "");
            });
        })
        .finally(() => {
            document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    Promise.all([serverConfigPromise, rolesPromise])
        .then((configs) => {
            let serverConfig = configs[0];
            let roles = configs[1];

            $.each(serverConfig.attacks, function (factionid, factionConfig) {
                $.each(factionConfig.retal.roles, function (index, role) {
                    let option = $(`.faction-retal-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if (option.length !== 1) {
                        return;
                    }

                    option.attr("selected", "");
                });

                $.each(factionConfig.chain_bonus.roles, function (index, role) {
                    let option = $(`.faction-bonus-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if (option.length !== 1) {
                        return;
                    }

                    option.attr("selected", "");
                });

                $.each(factionConfig.chain_alert.roles, function (index, role) {
                    let option = $(`.faction-alert-roles[data-faction="${factionid}"] option[value="${role}"]`);

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
        })
        .finally(() => {
            document.querySelectorAll(".discord-role-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                    plugins: ["remove_button"],
                });
            });
        });

    $('[data-bs-toggle="tooltip"]').tooltip({
        container: ".list-group",
    });

    Array.from(document.getElementsByClassName("faction-overdose-channel")).forEach((channelSelector) => {
        channelSelector.addEventListener("change", setOverdoseChannel);
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

    $(".faction-retal-channel").on("change", function () {
        tfetch("POST", `bot/${guildid}/attacks/retal/${this.getAttribute("data-faction")}/channel`, {
            body: {
                channel: this.options[this.selectedIndex].value,
            },
            errorTitle: "Retal Channel Set Failed",
        }).then(() => {
            generateToast("Retal Channel Set Successful");
        });
    });

    $(".faction-retal-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", `bot/${guildid}/attacks/retal/${this.getAttribute("data-faction")}/roles`, {
            body: {
                roles: selectedRoles,
            },
            errorTitle: "Retal Roles Add Failed",
        }).then((response) => {
            generateToast("Retal Role Add Successful");
        });
    });

    $(".faction-bonus-channel").on("change", function () {
        tfetch("POST", `bot/${guildid}/attacks/chain-bonus/${this.getAttribute("data-faction")}/channel`, {
            body: {
                channel: this.options[this.selectedIndex].value,
            },
            errorTitle: "Chain Bonus Channel Set Failed",
        }).then((response) => {
            generateToast("Chain Bonus Channel Set Successful");
        });
    });

    $(".faction-bonus-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", `bot/${guildid}/attacks/chain-bonus/${this.getAttribute("data-faction")}/roles`, {
            body: {
                roles: selectedRoles,
            },
            errorTitle: "Chain Bonus Roles Add Failed",
        }).then((response) => {
            generateToast("Chain Bonus Role Add Successful");
        });
    });

    $(".faction-bonus-length").on("change", function () {
        tfetch("POST", `bot/${guildid}/attacks/chain-bonus/${this.getAttribute("data-faction")}/length`, {
            body: {
                length: this.options[this.selectedIndex].value,
            },
            errorTitle: "Chain Bonus Length Set Failed",
        }).then((response) => {
            generateToast("Chain Bonus Length Set Successful");
        });
    });

    $(".faction-alert-channel").on("change", function () {
        tfetch("POST", `bot/${guildid}/attacks/chain-alert/${this.getAttribute("data-faction")}/channel`, {
            body: {
                channel: this.options[this.selectedIndex].value,
            },
            errorTitle: "Chain Alert Channel Set Failed",
        }).then((response) => {
            generateToast("Chain Alert Channel Set Successful");
        });
    });

    $(".faction-alert-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", `bot/${guildid}/attacks/chain-alert/${this.getAttribute("data-faction")}/roles`, {
            body: {
                roles: selectedRoles,
            },
            errorTitle: "Chain Alert Roles Add Failed",
        }).then((response) => {
            generateToast("Chain Alert Role Add Successful");
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

        tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-faction")}/banking`, {
            body: { roles: selectedRoles },
            errorTitle: "Banking Roles Add Failed",
        }).then((response) => {
            generateToast("Banking Roles Set Successful");
        });
    });
});

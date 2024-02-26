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
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true,
    });

    let configPromise = tfetch("GET", `bot/server/${guildid}`, { errorTitle: "Failed to Load Server Config" });
    let rolesPromise = rolesRequest();
    let channelsPromise = channelsRequest();

    let serverConfig;

    Promise.all([configPromise, rolesPromise])
        .then((response) => {
            serverConfig = response[0];

            $.each(serverConfig.verify.verified_roles, function (index, role) {
                let option = $(`#verification-roles option[value="${role}"]`);

                if (option.length === 0) {
                    return;
                }

                option.attr("selected", "");
            });

            $.each(serverConfig.verify.exclusion_roles, function (index, role) {
                let option = $(`#exclusion-roles option[value="${role}"]`);

                if (option.length === 0) {
                    return;
                }

                option.attr("selected", "");
            });

            $.each(serverConfig.verify.faction_verify, function (factionid, factionConfig) {
                $.each(factionConfig["roles"], function (index, role) {
                    let option = $(`.verification-faction-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if (option.length === 0) {
                        return;
                    }

                    option.attr("selected", "");
                });
            });
        })
        .finally(function () {
            $(".discord-role-selector").selectpicker();
        });

    Promise.all([configPromise, channelsPromise])
        .then((response) => {
            let logChannel = $(`#verification-log-channel option[value="${serverConfig.verify.log_channel}"]`);

            if (logChannel.length !== 0) {
                logChannel.attr("selected", "");
            }
        })
        .finally(function () {
            $(".discord-channel-selector").selectpicker();
        });

    $("#verification-config-enable").on("click", function () {
        tfetch("POST", "bot/verify", { body: { guildid: guildid }, errorTitle: "Verification Enable Failed" }).then(
            (response) => {
                generateToast(
                    "Verification Enable Successful",
                    "The Tornium API server has been successfully enabled."
                );
                $("#verification-config-enable").prop("disabled", true);
                $("#verification-config-disable").prop("disabled", false);
            }
        );
    });

    $("#verification-config-disable").on("click", function () {
        tfetch("DELETE", "bot/verify", { body: { guildid: guildid }, errorTitle: "Verification Disable Failed" }).then(
            (response) => {
                generateToast(
                    "Verification Disable Successful",
                    "The Tornium API server has been successfully enabled."
                );
                $("#verification-config-enable").prop("disabled", false);
                $("#verification-config-disable").prop("disabled", true);
            }
        );
    });

    $("#auto-verification-config-enable").on("click", function () {
        tfetch("POST", "bot/verify/auto", {
            body: { guildid: guildid },
            errorTitle: "Auto Verificable Enable Failed",
        }).then((response) => {
            generateToast(
                "Auto Verification Enable Successful",
                "The Tornium API server has been successfully enabled."
            );
            $("#auto-verification-config-enable").prop("disabled", true);
            $("#auto-verification-config-disable").prop("disabled", false);
        });
    });

    $("#auto-verification-config-disable").on("click", function () {
        tfetch("DELETE", "bot/verify/auto", {
            body: { guildid: guildid },
            errorTitle: "Auto Verification Disable Failed",
        }).then((response) => {
            generateToast(
                "Auto Verification Diable Successful",
                "The Tornium API server has been successfully enabled."
            );
            $("#auto-verification-config-enable").prop("disabled", false);
            $("#auto-verification-config-disable").prop("disabled", true);
        });
    });

    function addFactionVerify() {
        tfetch("POST", "bot/verify/faction", {
            body: { guildid: guildid, factiontid: $("#faction-verification-input").val() },
            errorTitle: "Verification Faction Set Failed",
        }).then((response) => {
            generateToast("Verification Faction Set Successful");
            window.location.reload(); // TODO: Replace with dynamically adding code
        });
    }

    $("#faction-verification-input").on("keypress", function (e) {
        if (e.which == 13) {
            addFactionVerify();
        }
    });
    $("#faction-verification-submit").on("click", addFactionVerify);

    $("#verification-log-channel").on("change", function () {
        tfetch("POST", "bot/verify/log", {
            body: { guildid: guildid, channel: this.options[this.selectedIndex].value },
            errorTitle: "Verification Log Channel Set Failed",
        }).then(() => {
            generateToast("Verification Log Channel Set Successful");
        });
    });

    $("#verification-name-template").on("keypress", function (e) {
        if (e.which !== 13) {
            return;
        }

        tfetch("POST", "bot/verify/template", {
            body: { guildid: guildid, template: $("#verification-name-template").val() },
            errorTitle: "Verification Template Set Failed",
        }).then(() => {
            generateToast("Verification Template Set Successful");
        });
    });

    $(".verification-faction-enable").on("click", function () {
        tfetch("POST", "bot/verify/faction", {
            body: { guildid: guildid, factiontid: this.getAttribute("data-faction") },
            errorTitle: "Faction Verification Enable Failed",
        }).then(() => {
            generateToast("Faction Verification Enable Successful");
            window.location.reload();
        });
    });

    $(".verification-faction-disable").on("click", function () {
        tfetch("DELETE", "bot/verify/faction", {
            body: { guildid: guildid, factiontid: this.getAttribute("data-faction") },
            errorTitle: "Faction Verification Disable Failed",
        }).then(() => {
            generateToast("Faction Verification Disable Successful");
            window.location.reload();
        });
    });

    $(".verification-faction-remove").on("click", function () {
        tfetch("DELETE", "bot/verify/faction", {
            body: { guildid: guildid, factiontid: this.getAttribute("data-faction"), remove: true },
            errorTitle: "Faction Verification Removal Failed",
        }).then(() => {
            generateToast("Faction Verification Removal Successful");
            window.location.reload();
        });
    });

    $(".verification-faction-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", `bot/verify/faction/${this.getAttribute("data-faction")}/roles`, {
            body: { guildid: guildid, roles: selectedRoles },
            errorTitle: "Faction Verification Role Set Failed",
        }).then(() => {
            generateToast("Faction Verification Role Set Successful");
        });
    });

    $("#verification-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", "bot/verify/roles", {
            body: { guildid: guildid, roles: selectedRoles },
            errorTitle: "Verification Role Add Failed",
        }).then(() => {
            generateToast("Verification Role Add Successful");
        });
    });

    $("#exclusion-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        tfetch("POST", "bot/verify/exclusion", {
            body: { guildid: guildid, roles: selectedRoles },
            errorTitle: "Verification Exlcusion Role Add Failed",
        }).then(() => {
            generateToast("Verification Exclusion Role Add Successful");
        });
    });

    $(".verification-faction-edit").on("click", function () {
        if ($("#verify-settings-modal").length != 0) {
            let modal = bootstrap.Modal.getInstance(document.getElementById("verify-settings-modal"));
            modal.dispose();
            $("#verify-settings-modal").remove();
        }

        const factionID = this.getAttribute("data-faction");

        tfetch("GET", `faction/positions?guildid=${guildid}&factiontid=${this.getAttribute("data-faction")}`, {
            errorTitle: "Position Load Failed",
        }).then((response) => {
            $.each(response.positions, function (index, position) {
                if (index % 2 == 0) {
                    $("#verify-settings-modal-body").append(
                        $("<div>", {
                            class: "row",
                            "data-row-index": Math.floor(index / 2),
                        })
                    );
                }

                $(`.row[data-row-index="${Math.floor(index / 2)}"]`).append(
                    $("<div>", {
                        class: "column col-sm-12 col-md-6",
                        "data-position": position._id,
                    })
                );
                $(`.column[data-position="${position._id}"]`).append(
                    $("<div>", {
                        class: "card mr-3 mb-3",
                        "data-position": position._id,
                        style: "background-color: inherit;",
                    })
                );
                $(`.card[data-position="${position._id}"]`).append(
                    $("<h5>", {
                        class: "card-header",
                        text: position.name,
                    })
                );
                $(`.card[data-position="${position._id}"]`).append(
                    $("<select>", {
                        class: "discord-role-selector faction-position-roles-selector",
                        "data-position": position._id,
                        "data-faction": position.factiontid,
                        "aria-label": `Roles for ${position.name}`,
                        "data-live-search": "true",
                        "data-selected-text-format": "count > 2",
                        multiple: "",
                        style: "background-color: inherit; border: transparent;",
                    })
                );
            });

            $.each(discordRoles, function (role_id, role) {
                $.each($(".faction-position-roles-selector"), function (index, item) {
                    if (
                        !Object.keys(serverConfig["verify"]["faction_verify"][factionID]["positions"]).includes(
                            item.getAttribute("data-position")
                        )
                    ) {
                        item.innerHTML += `<option value="${role.id}">${role.name}</option>`;
                    } else if (
                        serverConfig["verify"]["faction_verify"][factionID]["positions"][
                            item.getAttribute("data-position")
                        ].includes(role["id"])
                    ) {
                        item.innerHTML += `<option value="${role.id}" selected>${role.name}</option>`;
                    } else {
                        item.innerHTML += `<option value="${role.id}">${role.name}</option>`;
                    }
                });
            });

            $(".faction-position-roles-selector").on("change", function () {
                var selectedOptions = $(this).find(":selected");
                var selectedRoles = [];

                $.each(selectedOptions, function (index, item) {
                    selectedRoles.push(item.getAttribute("value"));
                });

                tfetch("POST", `bot/verify/faction/${factionID}/position/${this.getAttribute("data-position")}`, {
                    body: { guildid: guildid, roles: selectedRoles },
                    errorTitle: "Faction Position Role Add Failed",
                }).then(() => {
                    generateToast("Faction Position Role Add Successful");
                });
            });

            $(".discord-role-selector").selectpicker();
        });

        $("body").append(
            $("<div>", {
                class: "modal fade",
                id: "verify-settings-modal",
                tabindex: "-1",
                "aria-labelledby": "verify-settings-modal",
                "aria-hidden": "true",
            })
        );
        $("#verify-settings-modal").append(
            $("<div>", {
                class: "modal-dialog modal-xl",
                id: "verify-settings-modal-dialog",
            })
        );
        $("#verify-settings-modal-dialog").append(
            $("<div>", {
                class: "modal-content",
                id: "verify-settings-modal-content",
            })
        );
        $("#verify-settings-modal-content").append(
            $("<div>", {
                class: "modal-header",
                id: "verify-settings-modal-header",
            })
        );
        $("#verify-settings-modal-header").append(
            $("<h5>", {
                class: "modal-title",
                text: `Advanced Verification Dashboard: NYI [${this.getAttribute("data-faction")}]`,
            })
        );
        $("#verify-settings-modal-header").append(
            $("<button>", {
                type: "button",
                class: "btn-close",
                "data-bs-dismiss": "modal",
                "aria-label": "Close",
            })
        );
        $("#verify-settings-modal-content").append(
            $("<div>", {
                class: "modal-body container",
                id: "verify-settings-modal-body",
            })
        );

        let modal = new bootstrap.Modal($("#verify-settings-modal"));
        modal.show();
    });
});

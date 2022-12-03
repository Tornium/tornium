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

    let verificationConfig = null;
    let xhttp = new XMLHttpRequest();

    xhttp.onload = function() {
        let response = xhttp.response;

        if("code" in response) {
            generateToast("Discord Verification Config Not Located", response["message"]);
            generateToast("Verification Loading Halted", "The lack of verification configs has prevented the page from loading.")
            throw new Error("Verification config error");
        } else {
            verificationConfig = response;

            $.each(verificationConfig["verified_roles"], function(index, role) {
                let option = $(`#verification-roles option[value="${role}"]`);

                if(option.length === 0) {
                    return;
                }

                option.attr("selected", "");
            });

            $.each(verificationConfig["faction_verify"], function(factionid, factionConfig) {
                $.each(factionConfig["roles"], function(index, role) {
                    let option = $(`.verification-faction-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if(option.length === 0) {
                        return;
                    }

                    option.attr("selected", "");
                });
            });

            let logChannel = $(`#verification-log-channel option[value="${verificationConfig["verify_log_channel"]}"]`);

            if(logChannel.length !== 0) {
                logChannel.attr("selected", "");
            }
        }

        //     xhttp.onload = function() {
        //         let response = xhttp.response;
        //
        //         if("code" in response) {
        //             generateToast("Discord Roles Not Located", response["message"]);
        //         } else {
        //             roles = response["roles"];
        //
        //             $.each(response["roles"], function(role_id, role) {
        //                 if(verificationConfig["verified_roles"].includes(parseInt(role["id"]))) {
        //                     $("#verification-roles").get(0).innerHTML += `<option value="${role.id}" selected>${role.name}</option>`;
        //                 } else {
        //                     $("#verification-roles").get(0).innerHTML += `<option value="${role.id}">${role.name}</option>`;
        //                 }
        //
        //                 $.each($(".verification-faction-roles"), function(index, item) {
        //                     if(verificationConfig["faction_verify"][parseInt(item.getAttribute("data-faction"))]["roles"].includes(parseInt(role["id"]))) {
        //                         item.innerHTML += `<option value=${role.id}" selected>${role.name}</option>`;
        //                     } else {
        //                         item.innerHTML += `<option value=${role.id}>${role.name}</option>`;
        //                     }
        //                 });
        //             });
        //
        //             $(".discord-role-selector").selectpicker();
        //         }
        //
        //         xhttp.onload = function() {
        //             let response = xhttp.response;
        //
        //             if("code" in response) {
        //                 generateToast("Discord Channels Not Located", response["message"]);
        //             } else {
        //                 channels = response["channels"];
        //
        //                 $.each(response["channels"], function(category_id, category) {
        //                     let optgroup = $(`<optgroup>`);
        //                     optgroup.attr("label", category["name"]);
        //                     $("#verification-log-channel").append(optgroup);
        //
        //                     $.each(category["channels"], function(channel_id, channel) {
        //                         if(verificationConfig["verify_log_channel"] === parseInt(channel.id)) {
        //                             optgroup.append($(`<option value="${channel.id}" selected>#${channel.name}</option>`))
        //                         } else {
        //                             optgroup.append($(`<option value="${channel.id}">#${channel.name}</option>`));
        //                         }
        //                     });
        //                 });
        //
        //                 $(".discord-channel-selector").selectpicker();
        //             }
        //         }
        //
        //         xhttp.open("GET", `/api/bot/server/${guildid}/channels`);
        //         xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        //         xhttp.setRequestHeader("Content-Type", "application/json");
        //         xhttp.send();
        //     }
        //
        //     xhttp.open("GET", `/api/bot/server/${guildid}/roles`);
        //     xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        //     xhttp.setRequestHeader("Content-Type", "application/json");
        //     xhttp.send();
        // }
    }

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/bot/verify/${guildid}`);
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $("#verification-config-enable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Verification Enable Failed", `The Tornium API server has responded with \"${response["message"]}\".`)
            } else {
                generateToast("Verification Enable Successful", "The Tornium API server has been successfully enabled.")
                $("#verification-config-enable").prop("disabled", true);
                $("#verification-config-disable").prop("disabled", false);
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

    $(".verification-faction-enable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {

            } else {
                generateToast("Faction Enabled Successfully");
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify/faction");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factiontid": this.getAttribute("data-faction")
        }));
    });

    $(".verification-faction-disable").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {

            } else {
                generateToast("Faction Disabled Successfully");
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("DELETE", "/api/bot/verify/faction");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factiontid": this.getAttribute("data-faction")
        }));
    });

    $(".verification-faction-remove").on("click", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {

            } else {
                generateToast("Faction Removed Successfully");
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("DELETE", "/api/bot/verify/faction");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factiontid": this.getAttribute("data-faction"),
            "remove": true
        }));
    });


    $(".verification-faction-roles").on("change", function() {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function(index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Role Add Failed");
            } else {
                generateToast("Role Add Successful");
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/bot/verify/faction/${this.getAttribute("data-faction")}/roles`);
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "roles": selectedRoles
        }));
    });

    $("#verification-roles").on("change", function() {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function(index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Role Add Failed");
            } else {
                generateToast("Role Add Successful");
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/verify/roles");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "roles": selectedRoles
        }));
    });

    $(".verification-faction-edit").on("click", function() {
        if($('#verify-settings-modal').length != 0) {
            let modal = bootstrap.Modal.getInstance(document.getElementById('verify-settings-modal'));
            modal.dispose();
            $("#verify-settings-modal").remove();
        }

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Position Load Failed", response["message"]);
                return;
            }

            $.each(response["positions"], function(index, position) {
                if(index % 2 == 0) {
                    $("#verify-settings-modal-body").append($("<div>", {
                        "class": "row",
                        "data-row-index": Math.floor(index / 2)
                    }))
                }

                $(`.row[data-row-index="${Math.floor(index / 2)}"]`).append($("<div>", {
                    "class": "column col-sm-12 col-md-6",
                    "data-position": position._id
                }));
                $(`.column[data-position="${position._id}"]`).append($("<div>", {
                    "class": "card mr-3 mb-3",
                    "data-position": position._id
                }));
                $(`.card[data-position="${position._id}"]`).append($("<h5>", {
                    "class": "card-header",
                    "text": position.name
                }))
                $(`.card[data-position="${position._id}"]`).append($("<select>", {
                    "class": "discord-role-selector faction-position-roles-selector",
                    "data-position": position._id,
                    "data-faction": position.factiontid,
                    "aria-label": `Roles for ${position.name}`,
                    "data-live-search": "true",
                    "data-selected-text-format": "count > 2",
                    "multiple": "",
                }))
            });

            $.each(roles, function(role_id, role) {
                $.each($(".faction-position-roles-selector"), function(index, item) {
                    if(!(Object.keys(verificationConfig["faction_verify"][item.getAttribute("data-faction")]["positions"]).includes(item.getAttribute("data-position")))) {
                        console.log("Position not in config");
                        item.innerHTML += `<option value="${role.id}">${role.name}</option>`;
                    } else if(verificationConfig["faction_verify"][item.getAttribute("data-faction")]["positions"][item.getAttribute("data-position")].includes(role["id"])) {
                        console.log("Position in config");
                        item.innerHTML += `<option value="${role.id}" selected>${role.name}</option>`;
                    } else {
                        item.innerHTML += `<option value="${role.id}">${role.name}</option>`;
                    }
                });
            });

            $(".faction-position-roles-selector").on("change", function() {
                var selectedOptions = $(this).find(":selected");
                var selectedRoles = [];

                $.each(selectedOptions, function(index, item) {
                    selectedRoles.push(item.getAttribute("value"));
                });

                const xhttp = new XMLHttpRequest();

                xhttp.onload = function() {
                    let response = xhttp.response;

                    if("code" in response) {
                        generateToast("Role Add Failed");
                    } else {
                        generateToast("Role Add Successful");
                    }
                }

                xhttp.responseType = "json";
                xhttp.open("POST", `/api/bot/verify/faction/${this.getAttribute("data-faction")}/position/${this.getAttribute("data-position")}`);
                xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
                xhttp.setRequestHeader("Content-Type", "application/json");
                xhttp.send(JSON.stringify({
                    "guildid": guildid,
                    "roles": selectedRoles
                }));
            });

            $(".discord-role-selector").selectpicker();
        }

        xhttp.responseType = "json";
        xhttp.open("GET", `/api/faction/positions?guildid=${guildid}&factiontid=${this.getAttribute("data-faction")}`);
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();

        $("body").append($("<div>", {
            "class": "modal fade",
            "id": "verify-settings-modal",
            "tabindex": "-1",
            "aria-labelledby": "verify-settings-modal",
            "aria-hidden": "true"
        }));
        $("#verify-settings-modal").append($("<div>", {
            "class": "modal-dialog modal-xl",
            "id": "verify-settings-modal-dialog"
        }));
        $("#verify-settings-modal-dialog").append($("<div>", {
            "class": "modal-content",
            "id": "verify-settings-modal-content"
        }));
        $("#verify-settings-modal-content").append($("<div>", {
            "class": "modal-header",
            "id": "verify-settings-modal-header"
        }));
        $("#verify-settings-modal-header").append($("<h5>", {
            "class": "modal-title",
            "text": `Advanced Verification Dashboard: NYI [${this.getAttribute("data-faction")}]`
        }));
        $("#verify-settings-modal-header").append($("<button>", {
            "type": "button",
            "class": "btn-close",
            "data-bs-dismiss": "modal",
            "aria-label": "Close"
        }));
        $("#verify-settings-modal-content").append($("<div>", {
            "class": "modal-body container",
            "id": "verify-settings-modal-body"
        }));

        let modal = new bootstrap.Modal($("#verify-settings-modal"));
        modal.show();
    });
});

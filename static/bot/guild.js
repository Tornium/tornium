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

// const key = document.currentScript.getAttribute('data-key');
// const guildid = document.currentScript.getAttribute('data-guildid');
const assistMod = document.currentScript.getAttribute('data-assist-mod');

$(document).ready(function() {
    let serverConfig = null;
    let xhttp = new XMLHttpRequest();

    xhttp.onload = function() {
        let response = xhttp.response;

        if("code" in response) {
            generateToast("Server Config Not Loaded", response["message"]);
            throw new Error("Server config error");
        }

        serverConfig = response;

        channelsRequest().then(function() {
            console.log(serverConfig["assists"]["channel"]);
            console.log(`#assist-channel option[value="${serverConfig['assists']['channel']}"]`);
    
            let assistsChannel = $(`#assist-channel option[value="${serverConfig['assists']['channel']}"]`);
    
            console.log(assistsChannel);
    
            if(assistsChannel.length !== 0) {
                assistsChannel.attr("selected", "");
            }    
        }).finally(function() {
            $(".discord-channel-selector").selectpicker();
        });

        rolesRequest().then(function() {
            $.each(serverConfig["retals"], function(factionid, factionConfig) {
                $.each(factionConfig["roles"], function(index, role) {
                    let option = $(`.faction-retal-roles[data-faction="${factionid}"] option[value="${role}"]`);

                    if(option.length !== 1) {
                        return;
                    }

                    option.attr("selected", "");
                });
            });
        }).finally(function() {
            $(".discord-role-selector").selectpicker();
        });
    }
    
    xhttp.responseType = "json";
    xhttp.open("GET", `/api/bot/server/${guildid}`);
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $('[data-bs-toggle="tooltip"]').tooltip({
        container: '.list-group'
    });

    $('#assist-type-select').find('option').each(function(i, e) {
        if($(e).val() === String(assistMod)) {
            $('#assist-type-select').prop('selectedIndex', i);
        }
    });

    $('#stakeoutcategory').on('keypress', function(e) {
        if(e.which === 13) {
            const id = $('#stakeoutcategory').val();
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function() {
                window.location.reload();
            }

            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=category&value=${id}`);
            xhttp.send();
        }
    });

    $("#assist-channel").on("change", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Assists Channel Failed", response["message"]);
                return;
            }

            xhttp.responseType = "json";
            xhttp.open("POST", `/api/bot/${guildid}/assists/channel`);
            xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send(JSON.stringify({
                "channel": this.options[this.selectedIndex].value
            }));
        }
    })

    $('#assistfactionid').on('keypress', function(e) {
        if(e.which === 13) {
            const id = $('#assistfactionid').val();
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function() {
                window.location.reload();
            }

            xhttp.open('POST', `/bot/assists/${guildid}/update?action=faction&value=${id}`);
            xhttp.send();
        }
    });

    $('#submit-assist-mod').click(function() {
        const assistMod = $('#assist-type-select').val();
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            window.location.reload();
        }

        xhttp.open('POST', `/bot/assists/${guildid}/update?action=mod&value=${assistMod}`);
        xhttp.send();
    });

    $(".faction-retal-channel").on("change", function() {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("Channel Set Failed");
            } else {
                generateToast("Channel Set Successful");
                window.location.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/bot/retal/faction/channel");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factiontid": this.getAttribute("data-faction"),
            "channel": this.options[this.selectedIndex].value
        }));
    });

    $(".faction-retal-roles").on("change", function() {
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
        xhttp.open("POST", "/api/bot/retal/faction/roles");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            "guildid": guildid,
            "factiontid": this.getAttribute("data-faction"),
            "roles": selectedRoles
        }));
    })
});

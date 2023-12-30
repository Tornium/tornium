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
    let serverConfig = null;
    let xhttp = new XMLHttpRequest();

    xhttp.onload = function () {
        let response = xhttp.response;

        if ("code" in response) {
            generateToast("Server Config Not Loaded", response["message"]);
            throw new Error("Server config error");
        }

        serverConfig = response;

        channelsRequest()
            .then(function () {
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
            .finally(function () {
                $(".discord-channel-selector").selectpicker();
            });

        rolesRequest()
            .then(function () {
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
            .finally(function () {
                $(".discord-role-selector").selectpicker();
            });
    };

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/v1/bot/server/${guildid}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $('[data-bs-toggle="tooltip"]').tooltip({
        container: ".list-group",
    });

    function addFaction() {
        const xhttp = new XMLHttpRequest();
        let factiontid = $("#faction-id-input").val();

        xhttp.onload = function () {
            const response = xhttp.response;

            if ("code" in response) {
                generateToast("Faction Add Failed", response["message"]);
                return;
            }

            window.location.reload();
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/faction`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                factiontid: factiontid,
            })
        );
    }

    $("#faction-id-input").on("keypress", function (e) {
        if (e.which == 13) {
            addFaction();
        }
    });
    $("#faction-id-submit").on("click", addFaction);

    $(".remove-faction").on("click", function () {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            const response = xhttp.response;

            if ("code" in response) {
                generateToast("Faction Remove Failed", response["message"]);
                return;
            }

            window.location.reload();
        };

        xhttp.responseType = "json";
        xhttp.open("DELETE", `/api/v1/bot/${guildid}/faction`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                factiontid: this.getAttribute("data-factiontid"),
            })
        );
    });

    $("#assist-channel").on("change", function () {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Assists Channel Failed", response["message"]);
                return;
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/assists/channel`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                channel: this.options[this.selectedIndex].value,
            })
        );
    });

    function addAssistsFaction() {
        const id = $("#assist-faction-id").val();
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            window.location.reload();
        };

        xhttp.open("POST", `/bot/assists/${guildid}/update?action=faction&value=${id}`);
        xhttp.send();
    }

    $("#assist-faction-id").on("keypress", function (e) {
        if (e.which === 13) {
            addAssistsFaction;
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

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Role Add Failed");
            } else {
                generateToast("Role Add Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/assists/roles/${$(this).attr("id").split("-")[1]}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                roles: selectedRoles,
            })
        );
    });

    $(".faction-retal-channel").on("change", function () {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Channel Set Failed");
            } else {
                generateToast("Channel Set Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/v1/bot/retal/faction/channel");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                guildid: guildid,
                factiontid: this.getAttribute("data-faction"),
                channel: this.options[this.selectedIndex].value,
            })
        );
    });

    $(".faction-retal-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Role Add Failed");
            } else {
                generateToast("Role Add Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/v1/bot/retal/faction/roles");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                guildid: guildid,
                factiontid: this.getAttribute("data-faction"),
                roles: selectedRoles,
            })
        );
    });

    $(".faction-banking-channel").on("change", function () {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Channel Set Failed");
            } else {
                generateToast("Channel Set Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/faction/${this.getAttribute("data-faction")}/banking`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                channel: this.options[this.selectedIndex].value,
            })
        );
    });

    $(".faction-banking-roles").on("change", function () {
        var selectedOptions = $(this).find(":selected");
        var selectedRoles = [];

        $.each(selectedOptions, function (index, item) {
            selectedRoles.push(item.getAttribute("value"));
        });

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Role Set Failed");
            } else {
                generateToast("Role Set Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/faction/${this.getAttribute("data-faction")}/banking`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                roles: selectedRoles,
            })
        );
    });

    $(".stock-switch").on("change", function () {
        if ($("#percent-change-switch")[0].checked) {
            $("#percent-change-enabled").text("Enabled");
        } else {
            $("#percent-change-enabled").text("Disabled");
        }

        if ($("#cap-change-switch")[0].checked) {
            $("#cap-change-enabled").text("Enabled");
        } else {
            $("#cap-change-enabled").text("Disabled");
        }

        if ($("#new-day-price-switch")[0].checked) {
            $("#new-day-price-enabled").text("Enabled");
        } else {
            $("#new-day-price-enabled").text("Disabled");
        }

        if ($("#min-price-switch")[0].checked) {
            $("#min-price-enabled").text("Enabled");
        } else {
            $("#min-price-enabled").text("Disabled");
        }

        if ($("#max-price-switch")[0].checked) {
            $("#max-price-enabled").text("Enabled");
        } else {
            $("#max-price-enabled").text("Disabled");
        }

        const percentChange = $("#percent-change-switch")[0].checked;
        const capChange = $("#cap-change-switch")[0].checked;
        const newDayPrice = $("#new-day-price-switch")[0].checked;
        const minPrice = $("#min-price-switch")[0].checked;
        const maxPrice = $("#max-price-switch")[0].checked;

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Stock Config Update Failed");
            } else {
                generateToast("Stock Config Update Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/stocks/feed`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                percent_change: percentChange,
                cap_change: capChange,
                new_day_price: newDayPrice,
                min_price: minPrice,
                max_price: maxPrice,
            })
        );
    });

    $("#feed-channel").on("change", function () {
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Channel Set Failed");
            } else {
                generateToast("Channel Set Successful");
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/api/v1/bot/${guildid}/stocks/feed/channel`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                channel: this.options[this.selectedIndex].value,
            })
        );
    });
});

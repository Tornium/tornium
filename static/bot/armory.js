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

let channelsPromise = channelsRequest();
let itemsPromise = itemsRequest();
let rolesPromise = rolesRequest();

$(document).ready(function () {
    const xhttp = new XMLHttpRequest();

    xhttp.onload = function () {
        let serverConfig = xhttp.response;

        if ("code" in serverConfig) {
            generateToast(
                "Discord Config Not Located",
                serverConfig["message"]
            );
            generateToast(
                "Armory Tracker Loading Halted",
                "The lack of armory tracking configs has prevented the page from loading."
            );

            $("#tracked-factions-list").append(
                $("<p>", {
                    text: "Discord configuration failed to load...",
                })
            );
            $("#armory-faction-container").append(
                $("<p>", {
                    text: "Discord configuration failed to load...",
                })
            );

            return;
        }

        $.each(serverConfig.factions, function (factionID, factionData) {
            $("#tracked-factions-list").append(
                $("<li>", {
                    class: "list-group-item",
                    text: `${factionData.name} [${factionID}]`,
                }).append(
                    $("<button>", {
                        type: "button",
                        class: "btn btn-sm btn-outline armory-toggle-faction",
                        disabled: "disabled",
                        "data-faction": factionID,
                    }).append(
                        $("<i>", {
                            class: "fa-solid fa-spinner ",
                        })
                    )
                )
            );

            $("#armory-faction-container").append(
                $("<div>", {
                    class: "col-sm-12 col-xl-6 mt-3",
                }).append(
                    $("<div>", {
                        class: "card",
                    }).append([
                        $("<div>", {
                            class: "card-header",
                            text: `${factionData.name} [${factionID}]`,
                        }),
                        $("<div>", {
                            class: "card-body",
                        }).append([
                            $("<div>", {
                                class: "card",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "Tracker Channel",
                                }),
                                $("<div>", {
                                    class: "card-body",
                                }).append([
                                    $("<p>", {
                                        class: "card-text",
                                        text: "Select the channel armory tracking notifications are sent to",
                                    }),
                                    $("<select>", {
                                        class: "discord-channel-selector tracker-channel",
                                        "data-faction": factionID,
                                        "aria-label": "Armory Tracker Channel",
                                        "data-live-search": "true",
                                    }).append(
                                        $("<option>", {
                                            value: "0",
                                            text: "Disabled",
                                        })
                                    ),
                                ]),
                            ]),
                            $("<div>", {
                                class: "card mt-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "Armorer Roles",
                                }),
                                $("<div>", {
                                    class: "card-body",
                                }).append([
                                    $("<p>", {
                                        class: "card-text",
                                        text: "Select the roles for the factions' armorers",
                                    }),
                                    $("<select>", {
                                        class: "discord-role-selector armorer-roles",
                                        multiple: "true",
                                        "data-faction": factionID,
                                        "aria-label": "Armorer Roles",
                                        "data-live-search": "true",
                                        "data-selected-text-format":
                                            "count > 2",
                                    }),
                                ]),
                            ]),
                            $("<div>", {
                                class: "card mt-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "Tracked Items",
                                }),
                                $("<div>", {
                                    class: "card-body",
                                }).append([
                                    $("<ul>", {
                                        class: "list-group list-group-flush tracked-items",
                                        "data-faction": factionID,
                                    }),
                                    $("<p>", {
                                        class: "no-items-container me-3 text-end",
                                        text: "No items currently tracked...",
                                        "data-faction": factionID,
                                    }),
                                ]),
                                $("<div>", {
                                    class: "card-footer d-flex justify-content-end",
                                }).append(
                                    $("<div>", {
                                        class: "input-group mb-1",
                                    }).append([
                                        $("<select>", {
                                            class: "item-selector tracked-item",
                                            "aria-label":
                                                "Select item to be tracked",
                                            "data-live-search": "true",
                                        }),
                                        $("<input>", {
                                            type: "number",
                                            class: "form-control tracked-item-quantity",
                                            placeholder: "Quantity",
                                            min: "0",
                                            "aria-label":
                                                "Quantity notified when under",
                                        }),
                                        $("<button>", {
                                            type: "button",
                                            class: "btn btn-outline submit-new-item",
                                            text: "Track",
                                            "data-faction": factionID,
                                        }),
                                    ])
                                ),
                            ]),
                        ]),
                    ])
                )
            );
        });

        $.each(serverConfig.armory.config, function (factionID, factionConfig) {
            if (factionConfig.items.length > 0) {
                $(`.no-items-container[data-faction="${factionID}"]`).remove();
            }

            const trackedItems = $(
                `.tracked-items[data-faction="${factionID}"]`
            );
            $.each(factionConfig.items, function (itemID, itemQuantity) {
                trackedItems.append(
                    $("<li>", {
                        class: "list-group-item list-group-item-flush",
                        text: `${items[itemID]} >= ${commas(itemQuantity)}`,
                    })
                );
            });
        });

        if (serverConfig.armory.enabled) {
            $("#tracker-config-disable").removeAttr("disabled");
        } else {
            $("#tracker-config-enable").removeAttr("enabled");
        }

        itemsPromise.finally(function () {
            $(".item-selector").selectpicker();
        });

        channelsPromise
            .then(function () {
                $.each(
                    serverConfig.armory.config,
                    function (factionID, factionConfig) {
                        let option = $(
                            `.tracker-channel[data-faction="${factionID}"] option[value=${factionConfig.channel}]`
                        );

                        if (option.length !== 1) {
                            return;
                        }

                        option.attr("selected", "");
                    }
                );
            })
            .finally(function () {
                $(".discord-channel-selector").selectpicker();
            });

        rolesPromise
            .then(function () {
                $.each(
                    serverConfig.armory.config,
                    function (factionID, factionConfig) {
                        $.each(factionConfig.roles, function (index, roleID) {
                            let option = $(
                                `.armorer-roles[data-faction="${factionID}"] option[value=${roleID}]`
                            );

                            if (option.length !== 0) {
                                option.attr("selected", "");
                            }
                        });
                    }
                );
            })
            .finally(function () {
                $(".discord-role-selector").selectpicker();
            });

        $(".submit-new-item").on("click", function () {
            const xhttp = new XMLHttpRequest();
            let factionID = this.getAttribute("data-faction");
            let itemSelector = $(this).parent().find(".tracked-item");
            let itemID = itemSelector.options[itemSelector.selectedIndex].value;
            let minQuantity = $(this).parent().find(".tracked-item-quantity");

            xhttp.onload = function () {
                const response = xhttp.response;

                if ("code" in response) {
                    generateToast(
                        "New Item Tracking Failed",
                        response["message"]
                    );
                    return;
                }

                $(`.tracked-items[data-faction="${factionID}"]`).append(
                    $("<li>", {
                        class: "list-group-item list-group-flush",
                        text: `${items[itemID]} [${itemID}]`,
                    })
                );
            };

            xhttp.responseType = "json";
            xhttp.open("POST", `/api/bot/${guildid}/armory/${factionID}/item`);
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send(
                JSON.stringify({
                    item: itemID,
                    quantity: minQuantity,
                })
            );
        });

        $(".armorer-roles").on("change", function () {
            let selectedOptions = $(this).find(":selected");
            let selectedRoles = [];

            $.each(selectedOptions, function (index, item) {
                selectedRoles.push(item.getAttribute("value"));
            });

            const xhtttp = new XMLHttpRequest();

            xhttp.onload = function () {
                const response = xhttp.response;

                if ("code" in response) {
                    generateToast("Role Add Failed", response["message"]);
                }
            };

            xhttp.responseType = "json";
            xhttp.open("POST", `/api/bot/${guildid}/armory/${factionID}/roles`);
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send(
                JSON.stringify({
                    roles: selectedRoles,
                })
            );
        });

        $(".tracker-channel").on("submit", function () {
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function () {
                const response = xhttp.response;

                if ("code" in response) {
                    generateToast("Channel Set Failed", response["message"]);
                }
            };

            xhttp.responseType = "json";
            xhttp.open(
                "POST",
                `/api/bot/${guildid}/armory/${factionID}/channel`
            );
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send(
                JSON.stringify({
                    channel: this.options[this.selectedIndex].value,
                })
            );
        });

        $("#armory-toggle").on("click", function () {
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function () {
                const response = xhttp.response;

                if ("code" in repsonse) {
                    generateToast("Armory Toggle Failed", response["message"]);
                }
            };

            xhttp.responseType = "json";
            xhttp.open("PUT", `/api/bot/${guildid}/armory/${factionID}`);
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send(
                JSON.stringify({
                    enabled: $(this).attr("id") === "tracker-config-enable",
                })
            );
        });
    };

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/bot/server/${guildid}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();
});

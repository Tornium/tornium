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
    const xhttp = new XMLHttpRequest();
    let channelsPromise = channelsRequest();
    let itemsPromise = itemsRequest();

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
                        class: "btn btn-outline armory-toggle-faction",
                        disabled: "disabled",
                        "data-faction": factionID,
                    })
                )
            );

            $("#armory-faction-container").append(
                $("<div>", {
                    class: "col-sm-12 col-md-6 col-xl-4",
                }).append(
                    $("<div>", {
                        class: "card",
                    }).append([
                        $("<div>", {
                            class: "card-header",
                            text: `${factionData.name} [${factionID}],`,
                        }),
                        $("<div>", {
                            class: "card-body",
                        }).append([
                            $("<div>", {
                                class: "card mt-3",
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
                                    text: "Tracked Items",
                                }),
                                $("<div>", {
                                    class: "card-body",
                                }).append(
                                    $("<ul>", {
                                        class: "list-group list-group-flush tracked-items",
                                        "data-faction": factionID,
                                    })
                                ),
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
                                            "aria-label":
                                                "Quantity notified when under",
                                        }),
                                        $("<button>", {
                                            type: "button",
                                            class: "btn btn-outline submit-new-item",
                                            text: "Track new item",
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

        itemsPromise.finally(function () {
            $(".item-selector").selectpicker();
        });

        channelsPromise
            .then(function () {
                $.each(
                    serverConfig.armory,
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

        $("#submit-new-item").on("click", function () {
            const xhttp = new XMLHttpRequest();
            let factionID = this.getAttribute("data-faction");
            let itemSelector = $(this).parent().find(".tracked-item");
            let itemID = itemSelector.options[itemSelector.selectedIndex].value;

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
                })
            );
        });
    };

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/bot/server/${guildid}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();
});

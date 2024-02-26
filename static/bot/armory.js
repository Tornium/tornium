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
    function removeTrackedItem() {
        let item = $(this).attr("data-item");
        let faction = $(this).attr("data-faction");

        tfetch("DELETE", `bot/${guildid}/armory/${faction}/item`, {
            body: { item: item },
            errorTitle: "Item Removal Failed",
        }).then((response) => {
            $(`.remove-item[data-faction="${faction}"][data-item=${item}]`).parent().remove();
        });
    }

    tfetch("GET", `bot/server/${guildid}`, {})
        .then((serverConfig) => {
            $.each(serverConfig.factions, function (factionID, factionData) {
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
                                $("<div>").append([
                                    $("<button>", {
                                        type: "button",
                                        class: "btn btn-outline armory-faction-toggle me-2",
                                        "data-state": "1",
                                        "data-faction": factionID,
                                        text: "Enable",
                                    }),
                                    $("<button>", {
                                        type: "button",
                                        class: "btn btn-outline armory-faction-toggle",
                                        disabled: "",
                                        "data-state": "0",
                                        "data-faction": factionID,
                                        text: "Disable",
                                    }),
                                ]),
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
                                            text: "Select the channel armory tracking notifications are sent to.",
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
                                            text: "Select the roles for the faction's armorers.",
                                        }),
                                        $("<select>", {
                                            class: "discord-role-selector armorer-roles",
                                            multiple: "true",
                                            "data-faction": factionID,
                                            "aria-label": "Armorer Roles",
                                            "data-live-search": "true",
                                            "data-selected-text-format": "count > 2",
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
                                            class: "no-items-container text-end",
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
                                                "aria-label": "Select item to be tracked",
                                                "data-live-search": "true",
                                            }),
                                            $("<input>", {
                                                type: "number",
                                                class: "form-control tracked-item-quantity",
                                                placeholder: "Quantity",
                                                inputmode: "numeric",
                                                min: "0",
                                                style: "min-width: 100px",
                                                "aria-label": "Quantity notified when under",
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

            if (serverConfig.armory.enabled) {
                $("#tracker-config-enable").attr("disabled", true);
                $("#tracker-config-disable").attr("disabled", false);
            } else {
                $("#tracker-config-enable").attr("disabled", false);
                $("#tracker-config-disable").attr("disabled", true);
            }

            itemsRequest().finally(() => {
                $(".item-selector").selectpicker();

                $.each(serverConfig.armory.config, function (factionID, factionConfig) {
                    if (Object.keys(factionConfig.items).length > 0) {
                        $(`.no-items-container[data-faction="${factionID}"]`).remove();
                    }

                    const trackedItems = $(`.tracked-items[data-faction="${factionID}"]`);
                    $.each(factionConfig.items, function (itemID, itemQuantity) {
                        trackedItems.append(
                            $("<li>", {
                                class: "list-group-item list-group-flush d-flex justify-content-between",
                                text: `${items[itemID]} < ${commas(itemQuantity)}`,
                            }).append(
                                $("<button>", {
                                    class: "btn btn-sm btn-outline remove-item",
                                    type: "button",
                                    "data-faction": factionID,
                                    "data-item": itemID,
                                }).append(
                                    $("<i>", {
                                        class: "fa-solid fa-minus",
                                    })
                                )
                            )
                        );
                    });

                    if (factionConfig.enabled) {
                        $(`.armory-faction-toggle[data-faction="${factionID}"][data-state="0"]`).attr(
                            "disabled",
                            false
                        );
                        $(`.armory-faction-toggle[data-faction="${factionID}"][data-state="1"]`).attr("disabled", true);
                    }
                });

                $(".remove-item").on("click", removeTrackedItem);
            });

            channelsRequest()
                .then(function () {
                    $.each(serverConfig.armory.config, function (factionID, factionConfig) {
                        let option = $(
                            `.tracker-channel[data-faction="${factionID}"] option[value=${factionConfig.channel}]`
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
                    $.each(serverConfig.armory.config, function (factionID, factionConfig) {
                        $.each(factionConfig.roles, function (index, roleID) {
                            let option = $(`.armorer-roles[data-faction="${factionID}"] option[value=${roleID}]`);

                            if (option.length !== 0) {
                                option.attr("selected", "");
                            }
                        });
                    });
                })
                .finally(function () {
                    $(".discord-role-selector").selectpicker();
                });

            $(".submit-new-item").on("click", function () {
                let factionID = this.getAttribute("data-faction");
                let itemSelector = $(this).parent().find(".tracked-item");
                let itemID = parseInt(itemSelector.find(":selected").val());
                let minQuantity = $(this).parent().find(".tracked-item-quantity").val();

                tfetch("POST", `bot/${guildid}/armory/${factionID}/item`, {
                    body: { item: itemID, quantity: minQuantity },
                    errorTitle: "New Item Tracking Failed",
                }).then((response) => {
                    $(`.tracked-items[data-faction="${factionID}"]`).append(
                        $("<li>", {
                            class: "list-group-item list-group-flush d-flex justify-content-between",
                            text: `${items[itemID]} < ${commas(minQuantity)}`,
                        }).append(
                            $("<button>", {
                                class: "btn btn-sm btn-outline remove-item",
                                type: "button",
                                "data-faction": factionID,
                                "data-item": itemID,
                            }).append(
                                $("<i>", {
                                    class: "fa-solid fa-minus",
                                })
                            )
                        )
                    );
                    $(`.no-items-container[data-faction="${factionID}"]`).remove();
                    $(`.remove-item[data-faction="${factionID}"][data-item="${itemID}"]`).on(
                        "click",
                        removeTrackedItem
                    );
                });
            });

            $(".armorer-roles").on("change", function () {
                let selectedOptions = $(this).find(":selected");
                let selectedRoles = [];

                $.each(selectedOptions, function (index, item) {
                    selectedRoles.push(item.getAttribute("value"));
                });

                tfetch("POST", `bot/${guildid}/armory/${$(this).attr("data-faction")}/roles`, {
                    body: { roles: selectedRoles },
                    errorTitle: "Role Add Failed",
                }).then((response) => {});
            });

            $(".tracker-channel").on("change", function () {
                tfetch("POST", `bot/${guildid}/armory/${$(this).attr("data-faction")}/channel`, {
                    body: { channel: this.options[this.selectedIndex].value },
                    errorTitle: "Channel Set Failed",
                }).then((response) => {});
            });

            $(".armory-toggle").on("click", function () {
                let enabled = $(this).attr("id") === "tracker-config-enable";

                tfetch("PUT", `bot/${guildid}/armory`, {
                    body: { enabled: enabled },
                    errorTitle: "Armory Toggle Failed",
                }).then((response) => {
                    if (enabled) {
                        $("#tracker-config-enable").attr("disabled", true);
                        $("#tracker-config-disable").attr("disabled", false);
                    } else {
                        $("#tracker-config-enable").attr("disabled", false);
                        $("#tracker-config-disable").attr("disabled", true);
                    }
                });
            });

            $(".armory-faction-toggle").on("click", function () {
                let faction = $(this).attr("data-faction");
                let enabled = $(this).attr("data-state") === "1";

                tfetch("PUT", `bot/${guildid}/armory/${faction}`, {
                    body: { enabled: enabled },
                    errorTitle: "Armory Faction Toggle Failed",
                }).then((response) => {
                    if (enabled) {
                        $(`.armory-faction-toggle[data-faction="${faction}"][data-state="1"]`).attr("disabled", true);
                        $(`.armory-faction-toggle[data-faction="${faction}"][data-state="0"]`).attr("disabled", false);
                    } else {
                        $(`.armory-faction-toggle[data-faction="${faction}"][data-state="1"]`).attr("disabled", false);
                        $(`.armory-faction-toggle[data-faction="${faction}"][data-state="0"]`).attr("disabled", true);
                    }
                });
            });

            $(".remove-item").on("click", removeTrackedItem);
        })
        .catch((err) => {
            $("#armory-faction-container").append(
                $("<p>", {
                    text: "Discord configuration failed to load...",
                })
            );
        });
});

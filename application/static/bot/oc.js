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

    let configSetupLogic = configPromise
        .then((serverConfig) => {
            $.each(serverConfig.factions, function (faction, factionData) {
                console.log(faction);
                $("#card-container").append(
                    $("<div>", {
                        class: "card mt-3",
                        "data-factionid": faction,
                    }),
                );
                $(`div .card[data-factionid="${faction}"]`).append(
                    $("<div>", {
                        class: "card-body",
                        "data-factionid": faction,
                    }),
                );
                $(`div .card-body[data-factionid="${faction}"]`).append([
                    $("<h5>", {
                        class: "card-title",
                        text: `Organized Crime Notification Configuration for NYI [${faction}]`,
                    }),
                    $("<p>", {
                        class: "card-text",
                        text: "The channel used for notifications and the roles that can be pinged.",
                    }),
                    $("<div>", {
                        class: "row",
                    }).append([
                        $("<div>", {
                            class: "col-sm-12 col-md-8 col-xl-4 mt-2",
                        }).append(
                            $("<div>", {
                                class: "card my-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "OC Ready Channel",
                                }),
                                $("<div>", {
                                    class: "form-floating px-3 py-3",
                                }).append(
                                    $("<select>", {
                                        class: "discord-channel-selector oc-ready-channel",
                                        "data-factionid": faction,
                                        "aria-label": "OC Ready Channel",
                                        "data-live-search": "true",
                                    }).append(
                                        $("<option>", {
                                            value: "0",
                                            text: "Disabled",
                                        }),
                                    ),
                                ),
                            ]),
                        ),
                        $("<div>", {
                            class: "col-sm-12 col-md-8 col-xl-4 mt-2",
                        }).append(
                            $("<div>", {
                                class: "card my-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "OC Ready Roles",
                                }),
                                $("<div>", {
                                    class: "form-floating px-3 py-3",
                                }).append(
                                    $("<select>", {
                                        class: "discord-role-selector oc-ready-roles",
                                        "data-factionid": faction,
                                        "aria-label": "OC Ready Roles",
                                        "data-live-search": "true",
                                        "data-selected-text-format": "count > 2",
                                        multiple: "",
                                    }),
                                ),
                            ]),
                        ),
                    ]),
                    $("<div>", {
                        class: "row",
                    }).append([
                        $("<div>", {
                            class: "col-sm-12 col-md-8 col-xl-4 mt-2",
                        }).append(
                            $("<div>", {
                                class: "card my-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "OC Delay Channel",
                                }),
                                $("<div>", {
                                    class: "form-floating px-3 py-3",
                                }).append(
                                    $("<select>", {
                                        class: "discord-channel-selector oc-delay-channel",
                                        "data-factionid": faction,
                                        "aria-label": "OC Delay Channel",
                                        "data-live-search": "true",
                                    }).append(
                                        $("<option>", {
                                            value: "0",
                                            text: "Disabled",
                                        }),
                                    ),
                                ),
                            ]),
                        ),
                        $("<div>", {
                            class: "col-sm-12 col-md-8 col-xl-4 mt-2",
                        }).append(
                            $("<div>", {
                                class: "card my-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "OC Delay Roles",
                                }),
                                $("<div>", {
                                    class: "form-floating px-3 py-3",
                                }).append(
                                    $("<select>", {
                                        class: "discord-role-selector oc-delay-roles",
                                        "data-factionid": faction,
                                        "aria-label": "OC Delay Roles",
                                        "data-live-search": "true",
                                        "data-selected-text-format": "count > 2",
                                        multiple: "",
                                    }),
                                ),
                            ]),
                        ),
                    ]),
                    $("<div>", {
                        class: "row",
                    }).append([
                        $("<div>", {
                            class: "col-sm-12 col-md-8 col-xl-4 mt-2",
                        }).append(
                            $("<div>", {
                                class: "card my-3",
                            }).append([
                                $("<div>", {
                                    class: "card-header",
                                    text: "OC Initiated Channel",
                                }),
                                $("<div>", {
                                    class: "form-floating px-3 py-3",
                                }).append(
                                    $("<select>", {
                                        class: "discord-channel-selector oc-initiated-channel",
                                        "data-factionid": faction,
                                        "aria-label": "OC Initiated Channel",
                                        "data-live-search": "true",
                                    }).append(
                                        $("<option>", {
                                            value: "0",
                                            text: "Disabled",
                                        }),
                                    ),
                                ),
                            ]),
                        ),
                    ]),
                ]);
            });
        })
        .then(() => {
            let rolesPromise = rolesRequest();
            let channelsPromise = channelsRequest();

            Promise.all([configPromise, rolesPromise]).then((response) => {
                let serverConfig = response[0];

                $.each(serverConfig.oc, function (factionid, oc_config) {
                    $.each(oc_config.ready.roles, function (index, role) {
                        let roleElement = $(`.oc-ready-roles[data-factionid="${factionid}"] option[value="${role}"]`);

                        if (roleElement.length === 0) {
                            return;
                        }

                        roleElement.attr("selected", "");
                    });

                    $.each(oc_config.delay.roles, function (index, role) {
                        let roleElement = $(`.oc-delay-roles[data-factionid="${factionid}"] option[value="${role}"]`);

                        if (roleElement.length === 0) {
                            return;
                        }

                        roleElement.attr("selected", "");
                    });
                });

                document.querySelectorAll(".discord-role-selector").forEach((element) => {
                    new TomSelect(element, {
                        create: false,
                        plugins: ["remove_button"],
                    });
                });
            });

            Promise.all([configPromise, channelsPromise, configSetupLogic]).then((response) => {
                let serverConfig = response[0];

                $.each(serverConfig.oc, function (factionid, oc_config) {
                    let delayChannel = $(
                        `.oc-delay-channel[data-factionid="${factionid}"] option[value="${oc_config.delay.channel}"]`,
                    );
                    let readyChannel = $(
                        `.oc-ready-channel[data-factionid="${factionid}"] option[value="${oc_config.ready.channel}"]`,
                    );
                    let initiatedChannel = $(
                        `.oc-initiated-channel[data-factionid="${factionid}"] option[value="${oc_config.initiated.channel}"]`,
                    );

                    if (delayChannel.length !== 0) {
                        delayChannel.attr("selected", "");
                    }
                    if (readyChannel.length !== 0) {
                        readyChannel.attr("selected", "");
                    }
                    if (initiatedChannel.length !== 0) {
                        initiatedChannel.attr("selected", "");
                    }
                });

                document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                    new TomSelect(element, {
                        create: false,
                    });
                });
            });
        })
        .then(() => {
            $(".oc-ready-channel").on("change", function () {
                tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-factionid")}/oc/ready/channel`, {
                    body: { channel: this.options[this.selectedIndex].value },
                    errorTitle: "OC Ready Channel Set Failed",
                }).then(() => {});
            });

            $(".oc-ready-roles").on("change", function () {
                var selectedOptions = $(this).find(":selected");
                var selectedRoles = [];

                $.each(selectedOptions, function (index, item) {
                    selectedRoles.push(item.getAttribute("value"));
                });

                tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-factionid")}/oc/ready/roles`, {
                    body: { roles: selectedRoles },
                    errorTitle: "OC Ready Roles Set Failed",
                }).then(() => {});
            });

            $(".oc-delay-channel").on("change", function () {
                tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-factionid")}/oc/delay/channel`, {
                    body: { channel: this.options[this.selectedIndex].value },
                    errorTitle: "OC Delay Channel Set Failed",
                }).then(() => {});
            });

            $(".oc-delay-roles").on("change", function () {
                var selectedOptions = $(this).find(":selected");
                var selectedRoles = [];

                $.each(selectedOptions, function (index, item) {
                    selectedRoles.push(item.getAttribute("value"));
                });

                tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-factionid")}/oc/delay/roles`, {
                    body: { roles: selectedRoles },
                    errorTitle: "OC Delay Roles Set Failed",
                }).then(() => {});
            });

            $(".oc-initiated-channel").on("change", function () {
                tfetch("POST", `bot/${guildid}/faction/${this.getAttribute("data-factionid")}/oc/initiated/channel`, {
                    body: { channel: this.options[this.selectedIndex].value },
                    errorTitle: "OC Initiated Channel Set Failed",
                }).then(() => {});
            });
        });
});

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
    $("#chain-form").submit(function (e) {
        e.preventDefault();
        $("#chain-list-button").attr("disabled", true);
        $("#targets-container").empty();

        const xhttp = new XMLHttpRequest();
        var ff = Number($("#chain-ff").val());

        xhttp.onload = function () {
            var response = xhttp.response;

            if ("code" in response) {
                generateToast(
                    "Chain List Request Failed",
                    `The Tornium API server has responded with \"${response["message"]}\" to the submitted request.`
                );
                $("#chain-list-button").attr("disabled", false);
                return;
            }

            const fragment = document.createDocumentFragment();

            response.data.forEach(function (user) {
                let bsMinMax = bsRange(user.battlescore);

                $(fragment).append(
                    $("<div>", {
                        class: "col-sm-12 col-md-6 col-xl-4",
                    }).append(
                        $("<div>", {
                            class: "card mt-3",
                            "data-tid": user.tid,
                        }).append([
                            $("<div>", {
                                class: "card-body",
                            }).append([
                                $("<h5>", {
                                    class: "card-title",
                                    text: user.user.username,
                                }),
                                $("<h6>", {
                                    class: "card-subtitle mb-2",
                                    text: `Last Update: ${reltime(
                                        user.timeadded
                                    )}`,
                                }),
                            ]),
                            $("<ul>", {
                                class: "list-group list-group-flush",
                            }).append([
                                $("<li>", {
                                    class: "list-group-item",
                                    text: `Estimated Fair Fight: ${user.ff}`,
                                }),
                                $("<li>", {
                                    class: "list-group-item",
                                    text: `Estimated Respect: ${user.respect}`,
                                }),
                                $("<li>", {
                                    class: "list-group-item",
                                    text: `Minimum Estimated Stats: ${commas(
                                        bsMinMax[0]
                                    )}`,
                                }),
                                $("<li>", {
                                    class: "list-group-item",
                                    text: `Maximum Estimated Stats: ${commas(
                                        bsMinMax[1]
                                    )}`,
                                }),
                            ]),
                            $("<ul>", {
                                class: "list-group list-group-flush mt-2 d-none target-user-data",
                            }),
                            $("<div>", {
                                class: "card-footer my-1",
                            }).append([
                                $("<button>", {
                                    class: "btn btn-outline-primary refresh-target-data mx-1",
                                    "data-tid": user.tid,
                                }).append(
                                    $("<i>", {
                                        class: "fa-solid fa-rotate-right",
                                    })
                                ),
                                $("<button>", {
                                    class: "btn btn-outline-primary mx-1",
                                    onclick: `window.open("https://www.torn.com/profiles.php?XID=${user.tid}", "_blank")`,
                                }).append(
                                    $("<i>", {
                                        class: "fa-regular fa-address-card",
                                    })
                                ),
                                $("<button>", {
                                    class: "btn btn-outline-primary mx-1",
                                    onclick: `window.open("https://www.torn.com/loader.php?sid=attack&user2ID=${user.tid}", "_blank")`,
                                }).append(
                                    $("<i>", {
                                        class: "fa-solid fa-crosshairs",
                                    })
                                ),
                            ]),
                        ])
                    )
                );
            });

            $("#targets-container").append(fragment);

            $(".refresh-target-data").on("click", function () {
                $(this).attr("disabled", true);
                const userID = this.getAttribute("data-tid");
                const xhttp = new XMLHttpRequest();

                xhttp.onload = function () {
                    var response = xhttp.response;

                    if ("code" in response) {
                        generateToast(
                            "User Update Failed",
                            `The Tornium API server has responded with \"${response["message"]}\" to the submitted request.`
                        );
                        return;
                    }

                    const targetDataContainer = $(
                        `div[data-tid="${userID}"] .target-user-data`
                    );
                    let factionName;

                    if (response.faction === null) {
                        factionName = "None";
                    } else {
                        factionName = `${response.faction.name} [${response.faction.tid}]`;
                    }

                    targetDataContainer.append(
                        $("<ul>", {
                            class: "list-group list-group-flush",
                        }).append([
                            $("<li>", {
                                class: "list-group-item",
                                text: `Level: ${response.level}`,
                            }),
                            $("<li>", {
                                class: "list-group-item",
                                text: `Faction: ${factionName}`,
                            }),
                            $("<li>", {
                                class: "list-group-item",
                                text: `Status: ${response.status} (${reltime(
                                    response.last_action
                                )})`,
                            }),
                        ])
                    );

                    targetDataContainer.removeClass("d-none");
                };

                xhttp.responseType = "json";
                xhttp.open("GET", `/api/user/${userID}?refresh=true`);
                xhttp.setRequestHeader("Content-Type", "application/json");
                xhttp.send();
            });

            $("#chain-list-button").attr("disabled", false);
        };

        xhttp.responseType = "json";
        xhttp.open("GET", `/api/stat?ff=${ff}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();

        generateToast(
            "Chain List Request Sent",
            "The request for the chain list has been sent to the Tornium API server."
        );
    });
});

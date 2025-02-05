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

$(document).ready(function () {
    $(".difficulty-button").on("click", function () {
        if ($(this).hasClass("active")) {
            $(this).removeClass("active");
            return;
        } else if ($(".difficulty-button.active").length !== 0) {
            $(".difficulty-button.active").removeClass("active");
        }

        $(this).addClass("active");
    });

    $(".sorting-button").on("click", function () {
        if ($(this).hasClass("active")) {
            $(this).removeClass("active");
        } else if ($(".sorting-button.active").length !== 0) {
            $(".sorting-button.active").removeClass("active");
        }

        $(this).addClass("active");
    });

    $(".limit-button").on("click", function () {
        if ($(this).hasClass("active")) {
            $(this).removeClass("active");
        } else if ($(".limit-button.active").length !== 0) {
            $(".limit-button.active").removeClass("active");
        }

        $(this).addClass("active");
    });

    $("#generate-list").on("click", function () {
        let difficulty = $(".difficulty-button.active");
        const sorting = $(".sorting-button.active");
        const targets = $(".limit-button.active");
        let ff;
        let sort;

        if (difficulty.length === 0) {
            generateToast("Missing Config", "No difficulty was set.");
            return;
        } else if (sorting.length === 0) {
            generateToast("Missing Config", "No sort was set.");
            return;
        } else if (targets.length === 0) {
            generateToast("Missing Config", "No limit was set.");
            return;
        }

        difficulty = parseInt(difficulty.first()[0].getAttribute("data-difficulty"));

        switch (sorting.first()[0].id) {
            case "recently-updated-sort":
                sort = "timestamp";
                break;
            case "highest-respect-sort":
                sort = "respect";
                break;
            case "random-sort":
                sort = "random";
                break;
            default:
                generateToast("Invalid Sort", "Invalid sort option");
                return;
        }

        const limit = parseInt(targets.first()[0].getAttribute("data-limit"));

        $("#generate-list").attr("disabled", true);
        $("#targets-container").empty();

        tfetch("GET", `chain-list?difficulty=${difficulty}&sort=${sort}&limit=${limit}`, {
            errorTitle: "Chain List Request Failed",
        })
            .then((response) => {
                response["data"].sort((a, b) => parseFloat(b.respect) - parseFloat(a.respect));

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
                                        text: `Last Stat Update: ${reltime(user.timeadded)}`,
                                    }),
                                    $("<p>", {
                                        class: "card-subtitle mb-2",
                                        text: `Last User Update: ${reltime(user.user.last_refresh)}`,
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
                                        text: `Minimum Estimated Stats: ${commas(bsMinMax[0])}`,
                                    }),
                                    $("<li>", {
                                        class: "list-group-item",
                                        text: `Maximum Estimated Stats: ${commas(bsMinMax[1])}`,
                                    }),
                                ]),
                                $("<ul>", {
                                    class: "list-group list-group-flush mt-2",
                                }).append([
                                    $("<li>", {
                                        class: "list-group-item",
                                        text:
                                            user.user.faction.tid === null
                                                ? `Faction: None`
                                                : `Faction: ${user.user.faction.name} [${user.user.faction.tid}]`,
                                    }),
                                    $("<li>", {
                                        class: "list-group-item",
                                        text: `Last Action: ${reltime(user.user.last_action)}`,
                                    }),
                                ]),
                                $("<div>", {
                                    class: "card-footer my-1",
                                }).append([
                                    $("<button>", {
                                        class: "btn btn-outline-primary mx-1",
                                        onclick: `window.open("https://www.torn.com/profiles.php?XID=${user.tid}", "_blank")`,
                                    }).append(
                                        $("<i>", {
                                            class: "fa-regular fa-address-card",
                                        }),
                                    ),
                                    $("<button>", {
                                        class: "btn btn-outline-primary mx-1",
                                        onclick: `window.open("https://www.torn.com/loader.php?sid=attack&user2ID=${user.tid}", "_blank")`,
                                    }).append(
                                        $("<i>", {
                                            class: "fa-solid fa-crosshairs",
                                        }),
                                    ),
                                ]),
                            ]),
                        ),
                    );
                });

                $("#targets-container").append(fragment);
                $("#generate-list").attr("disabled", false);
            })
            .catch((err) => {
                $("#generate-list").attr("disabled", false);
                throw err;
            });

        generateToast(
            "Chain List Request Sent",
            "The request for the chain list has been sent to the Tornium API server.",
        );
    });
});

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

    xhttp.onload = function () {
        let moverData = xhttp.response;

        if ("code" in moverData) {
            generateToast(
                "Stock Movers Load Failed",
                `The Tornium API server has responded with \"${moverData["message"]}\" to the submitted request.`
            );
            $(".mover-data")
                .empty()
                .append(
                    $("<li>", {
                        class: "list-group-item",
                    }).append([
                        $("<i>", {
                            class: "fa-solid fa-circle-exclamation",
                            style: "color: #C83F49",
                        }),
                        $("<span>", {
                            class: "ps-2",
                            text: "Data failed to load.",
                        }),
                    ])
                );
            return;
        }

        xhttp.onload = function () {
            let stocksData = xhttp.response;

            if ("code" in stocksData) {
                generateToast(
                    "Stock Data Load Failed",
                    `The Tornium API server has responded with \"${stocksData["message"]}\" to the submitted request.`
                );
                $(".mover-data")
                    .empty()
                    .append(
                        $("<li>", {
                            class: "list-group-item",
                        }).append([
                            $("<i>", {
                                class: "fa-solid fa-circle-exclamation",
                                style: "color: #C83F49",
                            }),
                            $("<span>", {
                                class: "ps-2",
                                text: "Data failed to load.",
                            }),
                        ])
                    );
                return;
            }

            for (let n = 0; n < 5; n++) {
                $(`#gain-d1-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                stocksData[
                                    moverData.gainers.d1[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                moverData.gainers.d1[n].price
                            ).toFixed()}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "color: #32CD32",
                            text: `+${Number(
                                moverData.gainers.d1[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }

            for (let n = 0; n < 5; n++) {
                $(`#gain-d7-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                stocksData[
                                    moverData.gainers.d7[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                moverData.gainers.d7[n].price
                            ).toFixed()}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "color: #32CD32",
                            text: `+${Number(
                                moverData.gainers.d7[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }

            for (let n = 0; n < 5; n++) {
                $(`#gain-m1-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                stocksData[
                                    moverData.gainers.m1[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                moverData.gainers.m1[n].price
                            ).toFixed()}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "color: #32CD32",
                            text: `+${Number(
                                moverData.gainers.m1[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }

            for (let n = 0; n < 5; n++) {
                $(`#loss-d1-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                stocksData[
                                    moverData.losers.d1[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                moverData.losers.d1[n].price
                            ).toFixed()}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "color: #C83F49",
                            text: `${Number(
                                moverData.losers.d1[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }

            for (let n = 0; n < 5; n++) {
                $(`#loss-d7-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                stocksData[
                                    moverData.losers.d7[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                moverData.losers.d7[n].price
                            ).toFixed()}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "color: #C83F49",
                            text: `${Number(
                                moverData.losers.d7[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }

            for (let n = 0; n < 5; n++) {
                $(`#loss-m1-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                stocksData[
                                    moverData.losers.m1[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                moverData.losers.m1[n].price
                            ).toFixed()}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "color: #C83F49",
                            text: `${Number(
                                moverData.losers.m1[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }
        };

        xhttp.open("GET", "/api/stocks");
        xhttp.send();
    };

    xhttp.responseType = "json";
    xhttp.open("GET", "/api/stocks/movers");
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();
});

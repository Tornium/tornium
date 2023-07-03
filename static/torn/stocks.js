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

let STOCKS_DATA;
let MOVERS_DATA;
let BENEFITS_DATA;

let benefitsSorted = [];
let benefitsPage = 0;
let benefitsLoaded = false;

const stocksQuery = async function () {
    return fetch("/api/stocks", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    });
};

const moversQuery = async function () {
    return fetch("/api/stocks/movers", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    });
};

const benefitsQuery = async function () {
    return fetch("/api/stocks/benefits", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
    });
};

function renderStocksBenefitsPage() {
    if (!benefitsLoaded) {
        generateToast(
            "Benefits Render Failed",
            "The stock benefits haven't been loaded from the Tornium API yet."
        );
        return;
    }

    let benefitsListed = benefitsSorted.slice(
        6 * benefitsPage,
        6 * benefitsPage + 6
    );

    for (let i = 0; i < benefitsListed.length; i++) {
        let stock = STOCKS_DATA[benefitsListed[i]["stock_id"]];

        $(`#passive-${i} .card-header`)
            .empty()
            .append(
                $("<span>", {
                    text: `${stock.acronym} → Block #${benefitsListed[i].bb_n}`,
                })
            )
            .removeClass("placeholder");

        $(`#passive-${i} .card-text`)
            .empty()
            .text(
                `${stock.acronym} pays ${benefitsListed[i].description} every ${benefitsListed[i].frequency} days.`
            )
            .removeClass("placeholder");

        $(`#passive-${i} .list-group-flush`)
            .empty()
            .append([
                $("<li>", {
                    class: "list-group-item",
                    text: `Price: $${Number(stock.price).toFixed(2)}`,
                }),
                $("<li>", {
                    class: "list-group-item",
                    text: `Total Cost: $${commas(benefitsListed[i].cost)}`,
                }),
                $("<li>", {
                    class: "list-group-item",
                    text: `Average Daily Return: $${commas(
                        Number(
                            benefitsListed[i].value /
                                benefitsListed[i].frequency
                        ).toFixed(2)
                    )}`,
                }),
                $("<li>", {
                    class: "list-group-item",
                    text: `Yearly ROI: ${(
                        benefitsListed[i].daily_roi *
                        365 *
                        100
                    ).toFixed(2)}%`,
                }),
            ]);

        $(`#passive-${i} .benefit-tornsy`)
            .attr("href", `https://tornsy.com/${stock.acronym}/h6`)
            .removeClass("disabled");
    }

    if (benefitsListed.length < 6) {
        for (let i = benefitsListed.length - 1; i < 6; i++) {
            $(`#passive-${i}`).addClass("hidden");
        }
    }

    if (benefitsPage === 0) {
        $(".passives-previous-page").attr("disabled", "");
    } else if (benefitsPage === Math.ceil(benefitsSorted.length / 6)) {
        $(".passives-next-page").attr("disabled", "");
    } else {
        $(".passives-previous-page").removeAttr("disabled");
        $(".passives-next-page").removeAttr("disabled");
    }
}

$(document).ready(async function () {
    await Promise.all([await stocksQuery(), await benefitsQuery()])
        .then(async (response) => {
            STOCKS_DATA = await response[0].json();
            BENEFITS_DATA = await response[1].json();
        })
        .then(() => {
            if ("code" in STOCKS_DATA) {
                generateToast(
                    "Stock Data Load Failed",
                    `The Tornium API server has responded with \"${STOCKS_DATA["message"]}\" to the submitted request.`
                );
                $("[id^=passive-] .card-header")
                    .empty()
                    .removeClass("placeholder")
                    .append([
                        $("<i>", {
                            class: "fa-solid fa-circle-exclamation",
                            style: "color: #C83F49",
                        }),
                        $("<span>", {
                            class: "ps-2",
                            text: "Data failed to load.",
                        }),
                    ]);
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
                $("[id^=passive-] .card-text").hide();
                return { then: function () {} };
            } else if ("code" in BENEFITS_DATA) {
                generateToast(
                    "Stock Movers Load Failed",
                    `The Tornium API server has responded with \"${BENEFITS_DATA["message"]}\" to the submitted request.`
                );
                $("[id^=passive-] .card-header")
                    .empty()
                    .removeClass("placeholder")
                    .append([
                        $("<i>", {
                            class: "fa-solid fa-circle-exclamation",
                            style: "color: #C83F49",
                        }),
                        $("<span>", {
                            class: "ps-2",
                            text: "Data failed to load.",
                        }),
                    ]);
                $("[id^=passive-] .card-text").hide();
                throw undefined;
            }
        })
        .then(() => {
            BENEFITS_DATA["active"].forEach(function (stockBenefit) {
                for (let i = 1; i < 4; i++) {
                    let cost =
                        i *
                        stockBenefit["benefit"]["requirement"] *
                        STOCKS_DATA[stockBenefit["stock_id"]]["price"];
                    benefitsSorted.push({
                        stock_id: stockBenefit["stock_id"],
                        value: stockBenefit["benefit"]["value"],
                        description: stockBenefit["benefit"]["description"],
                        frequency: stockBenefit["benefit"]["frequency"],
                        cost: cost,
                        bb_n: i,
                        daily_roi:
                            stockBenefit["benefit"]["value"] /
                            stockBenefit["benefit"]["frequency"] /
                            cost,
                    });
                }
            });

            benefitsSorted = benefitsSorted.sort(function (f, s) {
                return s.daily_roi - f.daily_roi;
            });
            benefitsLoaded = true;
            renderStocksBenefitsPage();
        });

    await Promise.all([await stocksQuery(), await moversQuery()])
        .then(async (response) => {
            STOCKS_DATA = await response[0].json();
            MOVERS_DATA = await response[1].json();
        })
        .then(() => {
            if ("code" in STOCKS_DATA) {
                generateToast(
                    "Stock Data Load Failed",
                    `The Tornium API server has responded with \"${STOCKS_DATA["message"]}\" to the submitted request.`
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
                throw undefined;
            } else if ("code" in MOVERS_DATA) {
                generateToast(
                    "Stock Movers Load Failed",
                    `The Tornium API server has responded with \"${MOVERS_DATA["message"]}\" to the submitted request.`
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
                throw undefined;
            }
        })
        .then(() => {
            for (let n = 0; n < 5; n++) {
                $(`#gain-d1-${n}`)
                    .empty()
                    .append([
                        $("<span>", {
                            text: `${
                                STOCKS_DATA[
                                    MOVERS_DATA.gainers.d1[
                                        n
                                    ].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                MOVERS_DATA.gainers.d1[n].price
                            ).toFixed(2)}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "background-color: #32CD32 !important; color: white",
                            text: `+${Number(
                                MOVERS_DATA.gainers.d1[n].change * 100
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
                                STOCKS_DATA[
                                    MOVERS_DATA.gainers.d7[
                                        n
                                    ].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                MOVERS_DATA.gainers.d7[n].price
                            ).toFixed(2)}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "background-color: #32CD32 !important; color: white",
                            text: `+${Number(
                                MOVERS_DATA.gainers.d7[n].change * 100
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
                                STOCKS_DATA[
                                    MOVERS_DATA.gainers.m1[
                                        n
                                    ].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                MOVERS_DATA.gainers.m1[n].price
                            ).toFixed(2)}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "background-color: #32CD32 !important; color: white",
                            text: `+${Number(
                                MOVERS_DATA.gainers.m1[n].change * 100
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
                                STOCKS_DATA[
                                    MOVERS_DATA.losers.d1[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                MOVERS_DATA.losers.d1[n].price
                            ).toFixed(2)}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "background-color: #C83F49 !important; color: white",
                            text: `${Number(
                                MOVERS_DATA.losers.d1[n].change * 100
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
                                STOCKS_DATA[
                                    MOVERS_DATA.losers.d7[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                MOVERS_DATA.losers.d7[n].price
                            ).toFixed(2)}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "background-color: #C83F49 !important; color: white",
                            text: `${Number(
                                MOVERS_DATA.losers.d7[n].change * 100
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
                                STOCKS_DATA[
                                    MOVERS_DATA.losers.m1[n].stock_id.toString()
                                ].acronym
                            } → $${Number(
                                MOVERS_DATA.losers.m1[n].price
                            ).toFixed(2)}`,
                        }),
                        $("<span>", {
                            class: "badge bg-primary rounded-pill",
                            style: "background-color: #C83F49 !important; color: white",
                            text: `${Number(
                                MOVERS_DATA.losers.m1[n].change * 100
                            ).toFixed(2)}%`,
                        }),
                    ]);
            }
        });

    $(".passives-previous-page").on("click", function () {
        benefitsPage--;
        renderStocksBenefitsPage();
    });

    $(".passives-next-page").on("click", function () {
        benefitsPage++;
        renderStocksBenefitsPage();
    });
});

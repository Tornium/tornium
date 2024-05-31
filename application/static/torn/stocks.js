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

let benefitsSorted = [];
let benefitsPage = 0;
let benefitsLoaded = false;
let stocksData;

const stocksQuery = tfetch("GET", "stocks", { errorTitle: "Failed to Load Stocks" });
const moversQuery = tfetch("GET", "stocks/movers", { errorTitle: "Failed to Load Stock Movers" });
const benefitsQuery = tfetch("GET", "stocks/benefits", { errorTitle: "Failed to Load Stock Benefits" });

function renderStocksBenefitsPage() {
    if (!benefitsLoaded) {
        generateToast("Benefits Render Failed", "The stock benefits haven't been loaded from the Tornium API yet.");
        return;
    }

    let benefitsListed = benefitsSorted.slice(6 * benefitsPage, 6 * benefitsPage + 6);

    for (let i = 0; i < benefitsListed.length; i++) {
        let stock = stocksData[benefitsListed[i]["stock_id"]];

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
            .text(`${stock.acronym} pays ${benefitsListed[i].description} every ${benefitsListed[i].frequency} days.`)
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
                        parseInt(benefitsListed[i].value / benefitsListed[i].frequency)
                    )}`,
                }),
                $("<li>", {
                    class: "list-group-item",
                    text: `Yearly ROI: ${(benefitsListed[i].daily_roi * 365 * 100).toFixed(2)}%`,
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
    Promise.all([stocksQuery, benefitsQuery])
        .then((response) => {
            stocksData = response[0];
            let benefitsData = response[1];

            benefitsData.active.forEach(function (stockBenefit) {
                for (let i = 1; i < 4; i++) {
                    let cost = i * stockBenefit.benefit.requirement * stocksData[stockBenefit.stock_id]["price"];
                    benefitsSorted.push({
                        stock_id: stockBenefit.stock_id,
                        value: stockBenefit.benefit.value,
                        description: stockBenefit.benefit.description,
                        frequency: stockBenefit.benefit.frequency,
                        cost: cost,
                        bb_n: i,
                        daily_roi: stockBenefit.benefit.value / stockBenefit.benefit.frequency / cost,
                    });
                }
            });

            benefitsSorted = benefitsSorted.sort(function (f, s) {
                return s.daily_roi - f.daily_roi;
            });
            benefitsLoaded = true;
            renderStocksBenefitsPage();
        })
        .catch((err) => {
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
        });

    Promise.all([stocksQuery, moversQuery])
        .then((response) => {
            stocksData = response[0];
            let moversData = response[1];

            try {
                for (let n = 0; n < 5; n++) {
                    $(`#gain-d1-${n}`)
                        .empty()
                        .append([
                            $("<span>", {
                                text: `${
                                    stocksData[moversData.gainers.d1[n].stock_id.toString()].acronym
                                } → $${Number(moversData.gainers.d1[n].price).toFixed(2)}`,
                            }),
                            $("<span>", {
                                class: "badge bg-primary rounded-pill",
                                style: "background-color: #32CD32 !important; color: white",
                                text: `+${Number(moversData.gainers.d1[n].change * 100).toFixed(2)}%`,
                            }),
                        ]);
                }
            } catch (error) {
                console.log(error);
            }

            try {
                for (let n = 0; n < 5; n++) {
                    $(`#gain-d7-${n}`)
                        .empty()
                        .append([
                            $("<span>", {
                                text: `${
                                    stocksData[moversData.gainers.d7[n].stock_id.toString()].acronym
                                } → $${Number(moversData.gainers.d7[n].price).toFixed(2)}`,
                            }),
                            $("<span>", {
                                class: "badge bg-primary rounded-pill",
                                style: "background-color: #32CD32 !important; color: white",
                                text: `+${Number(moversData.gainers.d7[n].change * 100).toFixed(2)}%`,
                            }),
                        ]);
                }
            } catch (error) {
                console.log(error);
            }

            try {
                for (let n = 0; n < 5; n++) {
                    $(`#gain-m1-${n}`)
                        .empty()
                        .append([
                            $("<span>", {
                                text: `${
                                    stocksData[moversData.gainers.m1[n].stock_id.toString()].acronym
                                } → $${Number(moversData.gainers.m1[n].price).toFixed(2)}`,
                            }),
                            $("<span>", {
                                class: "badge bg-primary rounded-pill",
                                style: "background-color: #32CD32 !important; color: white",
                                text: `+${Number(moversData.gainers.m1[n].change * 100).toFixed(2)}%`,
                            }),
                        ]);
                }
            } catch (error) {
                console.log(error);
            }

            try {
                for (let n = 0; n < 5; n++) {
                    $(`#loss-d1-${n}`)
                        .empty()
                        .append([
                            $("<span>", {
                                text: `${stocksData[moversData.losers.d1[n].stock_id.toString()].acronym} → $${Number(
                                    moversData.losers.d1[n].price
                                ).toFixed(2)}`,
                            }),
                            $("<span>", {
                                class: "badge bg-primary rounded-pill",
                                style: "background-color: #C83F49 !important; color: white",
                                text: `${Number(moversData.losers.d1[n].change * 100).toFixed(2)}%`,
                            }),
                        ]);
                }
            } catch (error) {
                console.log(error);
            }

            try {
                for (let n = 0; n < 5; n++) {
                    $(`#loss-d7-${n}`)
                        .empty()
                        .append([
                            $("<span>", {
                                text: `${stocksData[moversData.losers.d7[n].stock_id.toString()].acronym} → $${Number(
                                    moversData.losers.d7[n].price
                                ).toFixed(2)}`,
                            }),
                            $("<span>", {
                                class: "badge bg-primary rounded-pill",
                                style: "background-color: #C83F49 !important; color: white",
                                text: `${Number(moversData.losers.d7[n].change * 100).toFixed(2)}%`,
                            }),
                        ]);
                }
            } catch (error) {
                console.log(error);
            }

            try {
                for (let n = 0; n < 5; n++) {
                    $(`#loss-m1-${n}`)
                        .empty()
                        .append([
                            $("<span>", {
                                text: `${stocksData[moversData.losers.m1[n].stock_id.toString()].acronym} → $${Number(
                                    moversData.losers.m1[n].price
                                ).toFixed(2)}`,
                            }),
                            $("<span>", {
                                class: "badge bg-primary rounded-pill",
                                style: "background-color: #C83F49 !important; color: white",
                                text: `${Number(moversData.losers.m1[n].change * 100).toFixed(2)}%`,
                            }),
                        ]);
                }
            } catch (error) {
                console.log(error);
            }
        })
        .catch((err) => {
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

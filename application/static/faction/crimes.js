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

let statusSpan = null;
let statusText = null;
let startCount = 0;
let queryLimit = 10;

function generateViewer() {
    statusSpan.text("Loading...");
    statusText.removeClass("d-none");

    let urlParams = new URLSearchParams();

    const limit = parseInt($("#data-limit").val());
    const selectedTypes = $("#data-oc-type").find(":selected");
    const fromTimestamp = $("#data-from-time").val();
    const toTimestamp = $("#data-to-time").val();
    const selectedParticipants = $("#data-participants").val();

    if (!Number.isNaN(limit) && limit != 10) {
        urlParams.set("limit", limit);
        queryLimit = limit;
    }

    if (selectedTypes.length > 0) {
        $.each(selectedTypes, function (index, crimeType) {
            urlParams.append("oc-type", crimeType.getAttribute("value"));
        });
    }

    if (fromTimestamp !== "") {
        urlParams.set("from-timestamp", Math.trunc(Date.parse(fromTimestamp) / 1000));
    }

    if (toTimestamp !== "") {
        urlParams.set("to-timestamp", Math.trunc(Date.parse(toTimestamp) / 1000));
    }

    if (selectedParticipants !== "") {
        selectedParticipants.split(",").forEach((participant) => {
            urlParams.append("participants", participant);
        });
    }

    if (startCount != 0) {
        urlParams.set("offset", startCount);
    }

    tfetch("GET", urlParams.size === 0 ? "faction/crimes" : "faction/crimes?" + urlParams.toString(), {
        errorTitle: "Faction OC Data Load Failed",
    })
        .then((response) => {
            if (response.crimes.length === 0) {
                statusSpan.text("No data available...");
                return;
            }

            statusSpan.text("Rendering...");

            let dataContainer = $("#oc-viewer-data");
            dataContainer.addClass("d-none");
            dataContainer.empty();

            $.each(response.crimes, function (index, crime) {
                console.log(crime);

                let participantsElement = $("<ul>", {
                    class: "list-group list-group-flush",
                });
                $.each(crime.participants, function (index, participant) {
                    let participantText = `${participant.name} [${participant.id}]`;

                    if (crime.delayers.includes(participant.id)) {
                        participantText += " - Delayer";
                    }

                    participantsElement.append(
                        $("<li>", {
                            class: "list-group-item",
                            text: participantText,
                        }),
                    );
                });

                let outcomeElement = $("<ul>", {
                    class: "list-group list-group-flush",
                });

                if (crime.money_gain !== null && crime.money_gain > 0) {
                    outcomeElement.append([
                        $("<li>", {
                            class: "list-group-item",
                            text: "Status: Success",
                        }),
                        $("<li>", {
                            class: "list-group-item",
                            text: `Money Gain: \$${commas(crime.money_gain)}`,
                        }),
                        $("<li>", {
                            class: "list-group-item",
                            text: `Respect Gain: ${commas(crime.respect_gain)}`,
                        }),
                    ]);
                } else if (crime.canceled) {
                    outcomeElement.append([
                        $("<li>", {
                            class: "list-group-item",
                            text: "Status: Canceled",
                        }),
                    ]);
                } else if (crime.time_ready >= Date.now() / 1000) {
                    outcomeElement.append([
                        $("<li>", {
                            class: "list-group-item",
                            text: "Status: In-Progress",
                        }),
                    ]);
                } else if (crime.time_completed !== null) {
                    outcomeElement.append([
                        $("<li>", {
                            class: "list-group-item",
                            text: "Status: Failure",
                        }),
                    ]);
                } else {
                    outcomeElement.append([
                        $("<li>", {
                            class: "list-group-item",
                            text: "Status: Unknown",
                        }),
                    ]);
                }

                let bodyElement = $("<div>", {
                    class: "accordion-body row",
                }).append(
                    $("<div>", {
                        class: "card col-md-6 col-lg-3 mx-2",
                    }).append([
                        $("<div>", {
                            class: "card-header fw-bold",
                            text: "Participants",
                        }),
                        participantsElement,
                    ]),
                    $("<div>", {
                        class: "card col-md-6 col-lg-3 mx-2",
                    }).append([
                        $("<div>", {
                            class: "card-header fw-bold",
                            text: "Outcome",
                        }),
                        outcomeElement,
                    ]),
                );

                let crimeHeader = crime.crime_type;

                if (crime.canceled) {
                    crimeHeader += " - Canceled";
                } else if (crime.delayers.length > 0) {
                    crimeHeader += " - Delayed";
                }

                if (crime.time_completed !== null && crime.money_gain != null && crime.money_gain > 0) {
                    crimeHeader += " - Success";
                } else if (crime.time_ready >= Date.now() / 1000) {
                    crimeHeader += " - In-Progress";
                } else if (crime.time_completed !== null) {
                    crimeHeader += " - Failure";
                }

                dataContainer.append(
                    $("<li>", {
                        class: "list-group-item accordion-item",
                    }).append([
                        $("<h6>", {
                            class: "accordion-header",
                        }).append(
                            $("<button>", {
                                class: "accordion-button collapsed",
                                type: "button",
                                text: crimeHeader,
                                "data-bs-toggle": "collapse",
                                "data-bs-target": `#oc-data-${crime.id}`,
                                "aria-expanded": false,
                                "aria-controls": `oc-data-${crime.id}`,
                            }),
                        ),
                        $("<div>", {
                            id: `oc-data-${crime.id}`,
                            class: "accordion-collapse collapse",
                            "data-bs-parent": "#oc-viewer-data",
                        }).append(bodyElement),
                    ]),
                );
            });

            dataContainer.removeClass("d-none");
            statusText.addClass("d-none");
        })
        .catch((err) => {
            statusSpan.text("Failed to load");
        });
}

$(document).ready(function () {
    statusSpan = $("#oc-viewer-status");
    statusText = $("#oc-status-text");

    new TomSelect("#data-oc-type", {
        create: false,
        createOnBlur: true,
        hideSelected: false,
    });
    new TomSelect("#data-participants", {
        persist: true,
        createOnBlur: true,
        create: true,
    });
    generateViewer();

    $("#generate-viewer").on("click", function () {
        startCount = 0;
        generateViewer();
    });

    $(".data-next-page").on("click", function () {
        startCount += queryLimit;
        $(".data-previous-page").prop("disabled", "");

        generateViewer();
    });

    $(".data-previous-page").on("click", function () {
        startCount -= queryLimit;

        if (startCount < 0) {
            startCount = 0;
        }

        if (startCount <= queryLimit) {
            $(".data-previous-page").prop("disabled", "disabled");
        }

        generateViewer();
    });
});

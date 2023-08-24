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
    let now = new Date();
    now = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    now.setMilliseconds(null);
    now.setSeconds(null);
    $("#end-time-input").val(now.toISOString().slice(0, -8));

    function addReport(item) {
        $("#existing-report-container").append(
            $("<div>", {
                class: "card mx-2 mt-2 report-card",
                "data-report-id": item.report_id,
            }).append(
                $("<div>", {
                    class: "row p-2",
                }).append([
                    $("<div>", {
                        class: "col-sm-12 col-md-4 col-xl-4 mt-1",
                        text: `${item.faction.name} [${item.faction.id}]`,
                    }),
                    $("<div>", {
                        class: "col-sm-12 col-md-6 col-xl-4 mt-1",
                        text: `${new Date(
                            item.start_timestamp * 1000
                        ).toLocaleString()} to ${new Date(
                            item.end_timestamp * 1000
                        ).toLocaleString()}`,
                    }),
                    $("<div>", {
                        class: "col-xl-3",
                    }),
                    $("<div>", {
                        class: "col-sm-12 col-md-2 col-xl-1 mt-1 justify-content-end d-flex",
                    }).append([
                        $("<button>", {
                            class: "btn btn-sm btn-outline-secondary view-report me-2",
                            "data-report-id": item.report_id,
                        }).append(
                            $("<i>", {
                                class: "fa-regular fa-eye",
                            })
                        ),
                        $("<button>", {
                            class: "btn btn-sm btn-outline-secondary delete-report",
                            "data-report-id": item.report_id,
                        }).append(
                            $("<i>", {
                                class: "fa-regular fa-trash-can",
                            })
                        ),
                    ]),
                ])
            )
        );
    }

    function deleteReport() {
        const rid = $(this).attr("data-report-id");
        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if (response.code === 1) {
                $(`.report-card[data-report-id="${rid}"]`).remove();
            }
        };

        xhttp.responseType = "json";
        xhttp.open("DELETE", `/api/report/faction/members/${rid}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    }

    function viewReport() {
        const rid = $(this).attr("data-report-id");
        window.location.href = `/torn/factions/member-report/${rid}`;
    }

    const xhttp = new XMLHttpRequest();

    xhttp.onload = function () {
        let response = xhttp.response;

        if ("code" in response) {
            generateToast(
                "Reports Load Failed",
                `The Tornium API server has responded with \"${response["message"]}\" to the submitted request.`
            );
            $("#existing-report-container")
                .empty()
                .append(
                    $("<i>", {
                        class: "fa-solid fa-skull-crossbones",
                        text: "Data failed to load...",
                    })
                );
            return;
        }

        $("#existing-report-container").empty();
        $.each(response.reports, function (index, item) {
            addReport(item);
        });

        $(".delete-report").on("click", deleteReport);
        $(".view-report").on("click", viewReport);
    };

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/report/faction/members`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $("#generate-report").on("click", function () {
        $("#generate-report").attr("disabled", true);

        const faction = $("#faction-id-input").val();
        let startTime = $("#start-time-input").val();
        let endTime = $("#end-time-input").val();
        let availability = $('input[name="data-availability"]:checked').val();

        if (availability === undefined) {
            availability = "user";
        }

        const selectedOptions = $("#ps-select").find(":selected");
        let selectedPS = [];

        $.each(selectedOptions, function (index, item) {
            selectedPS.push(item.text);
        });

        if (
            faction === "" ||
            startTime == "" ||
            endTime == "" ||
            selectedPS.length === 0 ||
            (availability !== "user" && availability !== "faction")
        ) {
            generateToast("Invalid Input", "An inputted value was not valid");
            $("#generate-report").attr("disabled", false);
            return;
        }

        startTime = Date.parse(startTime);
        endTime = Date.parse(endTime);

        if (startTime <= 0 || endTime <= 0) {
            generateToast(
                "Invalid Time",
                "An inputted date time was not valid"
            );
            $("#generate-report").attr("disabled", false);
            return;
        }

        const xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;
            $("#generate-report").attr("disabled", false);

            if ("code" in response) {
                generateToast(
                    "Report Generation Failed",
                    `The Tornium API server has responded with \"${response["message"]}\" to the submitted request.`
                );
                return;
            }

            addReport(response);
            $(".delete-report").on("click", deleteReport);
            $(".view-report").on("click", viewReport);
            $("#faction-id-input").val("");
            $("#start-time-input").val("");
            $("#end-time-input").val("");
        };

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/report/faction/members");
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                faction_id: faction,
                start_time: Math.floor(startTime / 1000),
                end_time: Math.floor(endTime / 1000),
                availability: availability,
                selected_stats: selectedPS,
            })
        );
    });
});

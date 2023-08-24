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

function median(sortedArray) {
    if (sortedArray.length === 0) {
        return;
    }

    const midPoint = Math.floor(sortedArray.length / 2);
    return sortedArray.length % 2 === 1
        ? sortedArray[midPoint]
        : (sortedArray[midPoint - 1] + sortedArray[midPoint]) / 2;
}

$(document).ready(function () {
    let response = null;
    let reportDataTable = null;
    let numMembers = null;

    function drawTable(stat) {
        let tableData = [];

        let startData = [];
        let endData = [];
        let diffData = [];

        let startSum = 0;
        let endSum = 0;
        let diffSum = 0;

        $.each(response.members, function (tid, member_data) {
            tableData.push([
                `${member_data.name} [${tid}]`,
                commas(response.start_data[tid][stat]),
                commas(response.end_data[tid][stat]),
                commas(
                    response.end_data[tid][stat] -
                        response.start_data[tid][stat]
                ),
            ]);

            startData.push(response.start_data[tid][stat]);
            endData.push(response.end_data[tid][stat]);
            diffData.push(
                response.end_data[tid][stat] - response.start_data[tid][stat]
            );

            startSum += response.start_data[tid][stat];
            endSum += response.end_data[tid][stat];
            diffSum +=
                response.end_data[tid][stat] - response.start_data[tid][stat];
        });

        startData.sort();
        endData.sort();
        diffData.sort();

        $("#start-sum").text(commas(startSum));
        $("#start-mean").text(commas(startSum / numMembers));
        $("#start-median").text(commas(median(startData)));

        $("#end-sum").text(commas(endSum));
        $("#end-mean").text(commas(endSum / numMembers));
        $("#end-median").text(commas(median(endData)));

        $("#diff-sum").text(commas(diffSum));
        $("#diff-mean").text(commas(diffSum / numMembers));
        $("#diff-median").text(commas(median(diffData)));

        reportDataTable.clear();
        reportDataTable.rows.add(tableData);
        reportDataTable.draw();
    }

    const xhttp = new XMLHttpRequest();
    const reportTable = $("#report-table");

    xhttp.onload = function () {
        response = xhttp.response;

        if ("code" in response) {
            generateToast(
                "Report Load Failed",
                `The Tornium API server has responded with \"${response["message"]}\" to the submitted request.`
            );
            $("#temp-container").text("The report failed to load...");
            return;
        }

        if (response.status < 2) {
            if (response.expected_end_time === undefined) {
                $("#temp-container").text(
                    "The report has not finished generating. Please try again later..."
                );
            } else {
                $("#temp-container").text(
                    `The report has not finished generating. The report should finish generating around ${new Date(
                        response.expected_end_time * 1000
                    ).toLocaleString()}. Please try again later...`
                );
            }
            return;
        }

        numMembers = Object.keys(response.members).length;

        reportTable.removeAttr("hidden");
        $.fn.dataTable.ext.pager.numbers_length = 5;
        reportDataTable = reportTable.DataTable({
            processing: false,
            serverSide: false,
            ordering: true,
            responsive: false,
            searching: true,
            scrollX: true,
            order: [[3, "desc"]],
            pagingType: "simple",
        });

        drawTable(response.requested_data[0]);
        $(`.stat-select[id="radio-${response.requested_data[0]}"]`).attr(
            "checked",
            ""
        );
        $("#report-stat-selector").removeAttr("hidden");
        $("#temp-container").hide();
        $("#stats-container").removeAttr("hidden");
        $("#selector-help").removeAttr("hidden");
        $("#selector-seperator").removeAttr("hidden");
    };

    xhttp.responseType = "json";
    xhttp.open(
        "GET",
        `/api/report/faction/members/${new URL(document.location.href).pathname
            .split("/")
            .at(-1)}`
    );
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();

    $(".stat-select").on("change", function () {
        drawTable($(this).attr("id").split("-")[1]);
    });
});

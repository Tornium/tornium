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

const battlescore = document.currentScript.getAttribute("data-battlescore");

$(document).ready(function () {
    var table = $("#stats-table").DataTable({
        processing: true,
        serverSide: true,
        ordering: true,
        responsive: false,
        ajax: {
            url: "/stats/dbdata",
            data: function (d) {
                d.minBS = $("#min-bs").val();
                d.maxBS = $("#max-bs").val();
            },
        },
        order: [
            [2, "desc"],
            [1, "desc"],
        ],
        pagingType: "simple",
        scrollX: true,
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $("#stats-table tbody").on("click", "tr", function () {
        if (battlescore === "-1") {
            generateToast("Permission Denied", "You must be signed in to access this feature.", "Error");
            return;
        }

        const xhttp = new XMLHttpRequest();
        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("User Retrieval Failed", response["message"], "Error");
                return;
            }

            $("#stats-modal-user-table").DataTable().destroy();
            $("#stats-modal-user-table").remove();
            $("#stat-modal-body").empty();

            const user = response["user"];
            let modal = new bootstrap.Modal($("#stats-modal"));

            let lastStat =
                response["stat_entries"][
                    Object.keys(response["stat_entries"])[Object.keys(response["stat_entries"]).length - 1]
                ];
            let ff = (1 + ((8 / 3) * lastStat["stat_score"]) / battlescore).toFixed(2);
            if (ff > 3) {
                ff = 3;
            }
            let respect = (((Math.log(user["level"]) + 1) / 4) * ff).toFixed(2);

            $("#stat-modal-body").append(
                $("<div>", {
                    class: "container",
                })
            );

            $("#stat-modal-body .container").append(
                $("<div>", {
                    class: "row",
                    id: "stat-modal-row-level",
                })
            );
            $("#stat-modal-row-level").append(
                $("<div>", {
                    class: "col-sm-4",
                    text: "Current Level:",
                })
            );
            $("#stat-modal-row-level").append(
                $("<div>", {
                    class: "col-sm-6",
                    text: `${user.level}`,
                })
            );

            $("#stat-modal-body .container").append(
                $("<div>", {
                    class: "row",
                    id: "stat-modal-row-faction",
                })
            );
            $("#stat-modal-row-faction").append(
                $("<div>", {
                    class: "col-sm-4",
                    text: "Faction:",
                })
            );

            if (user.faction === null) {
                $("#stat-modal-row-faction").append(
                    $("<div>", {
                        class: "col-sm-6",
                        text: `None`,
                    })
                );
            } else {
                $("#stat-modal-row-faction").append(
                    $("<div>", {
                        class: "col-sm-6",
                        text: `${user.faction.name} [${user.faction.tid}]`,
                    })
                );
            }

            $("#stat-modal-body .container").append(
                $("<div>", {
                    class: "row",
                    id: "stat-modal-row-last-action",
                })
            );
            $("#stat-modal-row-last-action").append(
                $("<div>", {
                    class: "col-sm-4",
                    text: "Last Action:",
                })
            );
            $("#stat-modal-row-last-action").append(
                $("<div>", {
                    class: "col-sm-6",
                    id: "stat-modal-last-action",
                })
            );
            $("#stat-modal-last-action").append(
                $("<span>", {
                    "data-bs-toggle": "tooltip",
                    "data-bs-placement": "right",
                    title: tcttime(user.last_action),
                    text: reltime(user.last_action),
                })
            );

            $("#stat-modal-body .container").append(
                $("<div>", {
                    class: "row",
                    id: "stat-modal-row-ff",
                })
            );
            $("#stat-modal-row-ff").append(
                $("<div>", {
                    class: "col-sm-4",
                    text: "Estimated Fair Fight:",
                })
            );
            $("#stat-modal-row-ff").append(
                $("<div>", {
                    class: "col-sm-6",
                    text: ff,
                })
            );

            $("#stat-modal-body .container").append(
                $("<div>", {
                    class: "row",
                    id: "stat-modal-row-respect",
                })
            );
            $("#stat-modal-row-respect").append(
                $("<div>", {
                    class: "col-sm-4",
                    text: "Estimated Respect:",
                })
            );
            $("#stat-modal-row-respect").append(
                $("<div>", {
                    class: "col-sm-6",
                    text: respect,
                })
            );

            $("#stat-modal-body .container").append(
                $("<div>", {
                    class: "row",
                    id: "stat-modal-row-last-refresh",
                })
            );
            $("#stat-modal-row-last-refresh").append(
                $("<div>", {
                    class: "col-sm-4",
                    text: "Last Refresh:",
                })
            );
            $("#stat-modal-row-last-refresh").append(
                $("<div>", {
                    class: "col-sm-6",
                    id: "stat-modal-last-refresh",
                })
            );
            $("#stat-modal-last-refresh").append(
                $("<span>", {
                    "data-bs-toggle": "tooltip",
                    "data-bs-placement": "right",
                    title: tcttime(user.last_refresh),
                    text: reltime(user.last_refresh),
                })
            );

            $("#stat-modal-label").text(`${user.name} [${user.tid}]`);
            $("#stat-modal-attack-link").attr("href", `https://www.torn.com/loader.php?sid=attack&user2ID=${user.tid}`);
            $("#stat-modal-profile-link").attr("href", `https://www.torn.com/profiles.php?XID=${user.tid}`);

            $("#stat-modal-body").append(
                $("<table>", {
                    id: "stats-modal-user-table",
                    class: "table table-striped table-bordered mt-3",
                })
            );
            $("#stats-modal-user-table").append($("<thead>"));
            $("#stats-modal-user-table thead").append($("<tr>"));
            $("#stats-modal-user-table thead tr").append(
                $("<th>", {
                    text: "Minimum Stats",
                })
            );
            $("#stats-modal-user-table thead tr").append(
                $("<th>", {
                    text: "Maximum Stats",
                })
            );
            $("#stats-modal-user-table thead tr").append(
                $("<th>", {
                    text: "Time Added",
                })
            );
            $("#stats-modal-user-table").append(
                $("<tbody>", {
                    id: "stats-modal-user-table-body",
                })
            );

            $.each(response["stat_entries"], function (stat_id, stat) {
                $("#stats-modal-user-table-body").append(
                    $("<tr>", {
                        "data-statid": stat_id,
                    })
                );

                let statRow = $(`tr[data-statid="${stat_id}"]`);

                statRow.append(
                    $("<th>", {
                        text: commas(bsRange(stat.stat_score)[0]),
                    })
                );
                statRow.append(
                    $("<th>", {
                        text: commas(bsRange(stat.stat_score)[1]),
                    })
                );
                statRow.append(
                    $("<th>", {
                        text: reltime(stat.timeadded),
                        "data-order": stat.timeadded,
                        "data-bs-toggle": "tooltip",
                        "data-bs-placement": "right",
                        title: tcttime(stat.timeadded),
                    })
                );
            });

            $('[data-bs-toggle="tooltip"]').tooltip({
                html: true,
            });

            modal.show();
            var statsTable = $("#stats-modal-user-table").DataTable({
                paging: true,
                ordering: true,
                responsive: false,
                autoWidth: false,
                order: [[2, "desc"]],
                scrollX: true,
            });

            setTimeout(function () {
                statsTable.columns.adjust();
                statsTable.responsive.recalc();
            }, 200);
        };

        xhttp.responseType = "json";
        xhttp.open("GET", `/api/v1/stat/${getTID(table.row(this).data()[0])}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    });

    $("#min-bs").on("change", function () {
        table.ajax.reload();
    });

    $("#max-bs").on("change", function () {
        table.ajax.reload();
    });
});

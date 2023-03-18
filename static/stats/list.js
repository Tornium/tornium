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

const key = document.currentScript.getAttribute('data-key');
let battlescore = null;

$(document).ready(function() {
    var targetTable = $('#targets-table').DataTable({
        "processing": true,
        "serverSide": false,
        "ordering": true,
        "responsive": false,
        "paging": true,
        "order": [[3, "desc"], [4, "desc"], [5, "desc"]],
        "columns": [
            {data: "name"},
            {data: "level"},
            {data: "ff"},
            {data: "respect"},
            {data: {_: "timeadded.display", sort: "timeadded.sort"}},
            {data: {_: "lastaction.display", sort: "lastaction.sort"}}
        ]
    });
    var targets = []

    $("#chainform").submit(function(e) {
        e.preventDefault();
        $("#chain-list-button").attr("disabled", true);

        const xhttp = new XMLHttpRequest();
        var value = Number($("#chainff").val());

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Chain List Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                xhttp.open("GET", "/api/user");
                xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
                xhttp.setRequestHeader("Content-Type", "application/json");
                xhttp.send();
                xhttp.onload = function() {
                    var userResponse = xhttp.response;
                    battlescore = userResponse["battlescore"];

                    if ("code" in userResponse) {
                        generateToast("Chain List Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
                        return;
                    }

                    response["data"].forEach(function(user) {
                        var ff = 1 + 8/3 * user["battlescore"] / userResponse["battlescore"];
                        ff = Math.min(ff, 3);
                        var baseRespect = ((Math.log(user["user"]["level"]) + 1)/4).toFixed(2);

                        if(!targets.includes(user["user"]["tid"])) {
                            targetTable.row.add({
                                name: user["user"]["username"],
                                level: user["user"]["level"],
                                ff: ff.toFixed(2),
                                respect: (ff * baseRespect).toFixed(2),
                                timeadded: {display: reltime(user["timeadded"]), sort: user["timeadded"]},
                                lastaction: {display: reltime(user["user"]["last_action"]), sort: user["user"]["last_action"]}
                            }).draw();

                            targets.push(user["user"]["tid"]);
                        }
                    });

                    targetTable.sort();
                    $("#chain-list-button").attr("disabled", false);
                }
            }
        }

        xhttp.responseType = "json";
        xhttp.open("GET", `/api/stat?ff=${value}`);
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();

        generateToast("Chain List Request Sent", "The request for the chain list has been sent to the Tornium API server.");
    });

    $('#targets-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("User Retrieval Failed", response["message"], "Error");
                return;
            }

            $("#stats-modal-user-table").DataTable().destroy();
            $("#stats-modal-user-table").remove();
            $("#stat-modal-body").empty();

            const user = response["user"];
            let modal = new bootstrap.Modal($("#stats-modal"));

            let lastStat = response["stat_entries"][Object.keys(response["stat_entries"])[Object.keys(response["stat_entries"]).length - 1]];
            let ff = 0;
            let respect = "Unknown"

            if(battlescore !== null) {
                ff = (1 + (8 / 3 * lastStat["stat_score"] / battlescore)).toFixed(2);
            }

            if(ff > 3) {
                ff = 3;
            }

            if(ff !== 0) {
                let respect = ((Math.log(user["level"]) + 1) / 4 * ff).toFixed(2);
            }

            $("#stat-modal-body").append($("<div>", {
                "class": "container"
            }));

            $("#stat-modal-body .container").append($("<div>", {
                "class": "row",
                "id": "stat-modal-row-level"
            }));
            $("#stat-modal-row-level").append($("<div>", {
                "class": "col-sm-4",
                "text": "Current Level:"
            }));
            $("#stat-modal-row-level").append($("<div>", {
                "class": "col-sm-6",
                "text": `${user.level}`
            }));

            $("#stat-modal-body .container").append($("<div>", {
                "class": "row",
                "id": "stat-modal-row-faction"
            }));
            $("#stat-modal-row-faction").append($("<div>", {
                "class": "col-sm-4",
                "text": "Faction:"
            }));

            if(user.faction === null) {
                $("#stat-modal-row-faction").append($("<div>", {
                    "class": "col-sm-6",
                    "text": `None`
                }));
            } else {
                $("#stat-modal-row-faction").append($("<div>", {
                    "class": "col-sm-6",
                    "text": `${user.faction.name} [${user.faction.tid}]`
                }));
            }

            $("#stat-modal-body .container").append($("<div>", {
                "class": "row",
                "id": "stat-modal-row-last-action"
            }));
            $("#stat-modal-row-last-action").append($("<div>", {
                "class": "col-sm-4",
                "text": "Last Action:"
            }));
            $("#stat-modal-row-last-action").append($("<div>", {
                "class": "col-sm-6",
                "id": "stat-modal-last-action"
            }));
            $("#stat-modal-last-action").append($("<span>", {
                "data-bs-toggle": "tooltip",
                "data-bs-placement": "right",
                "title": tcttime(user.last_action),
                "text": reltime(user.last_action)
            }));

            $("#stat-modal-body .container").append($("<div>", {
                "class": "row",
                "id": "stat-modal-row-ff"
            }));
            $("#stat-modal-row-ff").append($("<div>", {
                "class": "col-sm-4",
                "text": "Estimated Fair Fight:"
            }));
            $("#stat-modal-row-ff").append($("<div>", {
                "class": "col-sm-6",
                "text": ff
            }));

            $("#stat-modal-body .container").append($("<div>", {
                "class": "row",
                "id": "stat-modal-row-respect"
            }));
            $("#stat-modal-row-respect").append($("<div>", {
                "class": "col-sm-4",
                "text": "Estimated Respect:"
            }));
            $("#stat-modal-row-respect").append($("<div>", {
                "class": "col-sm-6",
                "text": respect
            }));

            $("#stat-modal-body .container").append($("<div>", {
                "class": "row",
                "id": "stat-modal-row-last-refresh"
            }));
            $("#stat-modal-row-last-refresh").append($("<div>", {
                "class": "col-sm-4",
                "text": "Last Refresh:"
            }));
            $("#stat-modal-row-last-refresh").append($("<div>", {
                "class": "col-sm-6",
                "id": "stat-modal-last-refresh"
            }));
            $("#stat-modal-last-refresh").append($("<span>", {
                "data-bs-toggle": "tooltip",
                "data-bs-placement": "right",
                "title": tcttime(user.last_refresh),
                "text": reltime(user.last_refresh)
            }));

            $("#stat-modal-label").text(`${user.name} [${user.tid}]`);
            $("#stat-modal-attack-link").attr("href", `https://www.torn.com/loader.php?sid=attack&user2ID=${user.tid}`);
            $("#stat-modal-profile-link").attr("href", `https://www.torn.com/profiles.php?XID=${user.tid}`);

            $("#stat-modal-body").append($("<table>", {
                "id": "stats-modal-user-table",
                "class": "table table-striped table-bordered mt-3"
            }));
            $("#stats-modal-user-table").append($("<thead>"));
            $("#stats-modal-user-table thead").append($("<tr>"));
            $("#stats-modal-user-table thead tr").append($("<th>", {
                "text": "Battlescore"
            }));
            $("#stats-modal-user-table thead tr").append($("<th>", {
                "text": "Time Added"
            }));
            $("#stats-modal-user-table thead tr").append($("<th>", {
                "text": "Added User"
            }));
            $("#stats-modal-user-table thead tr").append($("<th>", {
                "text": "Added Faction"
            }));
            $("#stats-modal-user-table").append($("<tbody>", {
                "id": "stats-modal-user-table-body"
            }));

            $.each(response["stat_entries"], function(stat_id, stat) {
                $("#stats-modal-user-table-body").append($("<tr>", {
                    "data-statid": stat_id
                }));

                let statRow = $(`tr[data-statid="${stat_id}"]`);

                statRow.append($("<th>", {
                    "text": commas(stat.stat_score)
                }));
                statRow.append($("<th>", {
                    "text": reltime(stat.timeadded),
                    "data-order": stat.timeadded,
                    "data-bs-toggle": "tooltip",
                    "data-bs-placement": "right",
                    "title": tcttime(stat.timeadded)
                }));

                if(stat.addedid === 0 || stat.addedid == null || stat.addeduser == null) {
                    statRow.append($("<th>", {
                        "text": "Unknown User"
                    }));
                } else {
                    statRow.append($("<th>", {
                        "text": `${stat.addeduser.name} [${stat.addedid}]`
                    }));
                }

                if(stat.addedfactiontid === 0) {
                    statRow.append($("<th>", {
                        "text": "Unknown/No Faction"
                    }));
                } else if(stat.addedfaction == null) {
                    statRow.append($("<th>", {
                        "text": `Unknown Faction ID ${stat.addedfactiontid}`
                    }));
                } else {
                    statRow.append($("<th>", {
                        "text": `${stat.addedfaction.name} [${stat.addedfactiontid}]`
                    }));
                }
            });

            $('[data-bs-toggle="tooltip"]').tooltip({
                html: true
            });

            modal.show();
            var statsTable = $('#stats-modal-user-table').DataTable({
                "paging": true,
                "ordering": true,
                "responsive": false,
                "autoWidth": false,
                "order": [[1, "desc"]],
                "scrollX": true
            });

            setTimeout(function() {
                statsTable.columns.adjust();
                statsTable.responsive.recalc();
            }, 200);
        }

        xhttp.responseType = "json";
        xhttp.open("GET", `/api/stat/${getTID(targetTable.row(this).data().name)}`);
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    });
});

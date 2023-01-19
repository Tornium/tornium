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

$(document).ready(function() {
    var targetTable = $('#targets-table').DataTable({
        "processing": true,
        "serverSide": false,
        "ordering": true,
        "responsive": true,
        "paging": true,
        "order": [[3, "desc"], [4, "desc"], [5, "desc"]]
    });
    var targets = []

    $("#chainform").submit(function(e) {
        e.preventDefault();
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

                    if ("code" in userResponse) {
                        generateToast("Chain List Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
                    } else {
                        response["data"].forEach(function(user) {
                            var ff = 1 + 8/3 * user["battlescore"] / userResponse["battlescore"];
                            ff = Math.min(ff, 3);
                            var baseRespect = ((Math.log(user["user"]["level"]) + 1)/4).toFixed(2);

                            if(!targets.includes(user["user"]["tid"])) {
                                targetTable.row.add([
                                    user["user"]["username"],
                                    user["user"]["level"],
                                    ff.toFixed(2),
                                    (ff * baseRespect).toFixed(2),
                                    reltime(user["timeadded"]),
                                    reltime(user["user"]["last_action"])
                                ]).draw();
                                targets.push(user["user"]["tid"]);
                            }
                        });

                        targetTable.sort();

                        $('#targets-table tbody').on('click', 'tr', function() {
                            const xhttp = new XMLHttpRequest();
                            xhttp.onload = function() {
                                if($('#stats-modal').length) {
                                    var modal = bootstrap.Modal.getInstance(document.getElementById('stats-modal'));
                                    modal.dispose();
                                }

                                document.getElementById('modal').innerHTML = this.responseText;
                                var modal = new bootstrap.Modal($('#stats-modal'));
                                $('#user-table').DataTable({
                                    "paging": true,
                                    "ordering": true,
                                    "responsive": true,
                                    "autoWidth": false,
                                    "order": [[0, "desc"]]
                                });
                                modal.show();
                            }

                            xhttp.open('GET', '/stats/userdata?user=' + targetTable.row(this).data()[0]);
                            xhttp.send();
                        });
                    }
                }
            }
        }

        xhttp.responseType = "json";
        xhttp.open("GET", "/api/stat");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'dstats': value
        }));
    });
});

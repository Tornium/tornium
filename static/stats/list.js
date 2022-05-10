/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

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

            function formatTS(timestamp) {
                console.log(timestamp)
                var tsAdded = new Date(timestamp * 1000);
                tsAdded = `${("0" + tsAdded.getHours()).slice(-2)}:${("0" + tsAdded.getMinutes()).slice(-2)}:${("0" + tsAdded.getSeconds()).slice(-2)} - ${("0" + tsAdded.getDate()).slice(-2)}/${("0" + tsAdded.getMonth()).slice(-2)}/${tsAdded.getUTCFullYear()}`;
                return tsAdded
            }

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
                                    modal.dispose;
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

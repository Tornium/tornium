/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const key = document.currentScript.getAttribute('data-key');

$(document).ready(function() {
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
                    const table = document.querySelector('#chain-table')
                    document.getElementById('chain-table-body').innerHTML = "";
                    var counter = 1

                    if ("code" in userResponse) {
                        response["data"].forEach(function(user) {
                            console.log(user)
                            var tableBody = document.getElementById('chain-table-body');
                            var newNode = document.createElement('tr');

                            newNode.innerHTML = `
                            <tr>
                                <th scope="col">${counter}</th>
                                <th scope="col">Error</th>
                                <th scope="col">Error</th>
                                <th scope="col">Error</th>
                                <th scope="col">${formatTS(user["timeadded"])}</th>
                                <th scope="col">${formatTS(user["user"]["last_action"])}</th>
                                <th scope="col">
                                    <a href="https://www.torn.com/loader.php?sid=attack&user2ID=${user['tid']}">
                                        <i class="fas fa-crosshairs"></i>
                                    </a>
                                    
                                    <a href="https://www.torn.com/profiles.php?XID=${user['tid']}">
                                        <i class="fas fa-id-card-alt"></i>
                                    </a>
                                </th>
                            </tr>
                            `;
                            tableBody.appendChild(newNode);
                            counter += 1;
                        });
                    } else {
                        response["data"].forEach(function(user) {
                            console.log(user)
                            var tableBody = document.getElementById('chain-table-body');
                            var newNode = document.createElement('tr');

                            var ff = 1 + 8/3 * user["battlescore"] / userResponse["battlescore"];
                            ff = Math.min(ff, 3);
                            var baseRespect = ((Math.log(user["user"]["level"]) + 1)/4).toFixed(2);

                            newNode.innerHTML = `
                            <tr>
                                <th scope="col">${counter}</th>
                                <th scope="col">${user["user"]["username"]}</th>
                                <th scope="col">${ff.toFixed(2)}</th>
                                <th scope="col">${(ff * baseRespect).toFixed(2)}</th>
                                <th scope="col">${formatTS(user["timeadded"])}</th>
                                <th scope="col">${formatTS(user["user"]["last_action"])}</th>
                                <th scope="col">
                                    <a href="https://www.torn.com/loader.php?sid=attack&user2ID=${user['tid']}">
                                        <i class="fas fa-crosshairs"></i>
                                    </a>
                                    
                                    <a href="https://www.torn.com/profiles.php?XID=${user['tid']}">
                                        <i class="fas fa-id-card-alt"></i>
                                    </a>
                                </th>
                            </tr>
                            `;
                            tableBody.appendChild(newNode);
                            counter += 1;
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

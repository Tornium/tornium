/* This file is part of Tornium.

Tornium is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Tornium is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Tornium.  If not, see <https://www.gnu.org/licenses/>. */

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

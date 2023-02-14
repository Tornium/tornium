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
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true
    });

    $('#banking-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/faction/userbankingdata"
        },
        "scrollX": true
    });

    $.fn.dataTable.ext.pager.numbers_length = 5;

    var xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        var response = xhttp.response;

        if("code" in response) {
            generateToast("Balance Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            $('#money-balance').val("ERROR");
            $('#points-balance').val("ERROR");
        } else {
            $('#money-balance').text(commas(response["money_balance"]));
            $('#points-balance').text(commas(response["points_balance"]));
        }
    }

    xhttp.responseType = "json";
    xhttp.open("GET", "/api/faction/banking/vault");
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send()


    $("#requestform").submit(function(e) {
        e.preventDefault();
        xhttp = new XMLHttpRequest();
        var value = $("#requestamount").val();
        value = value.toLowerCase();

        if(value !== "all") {
            var stringvalue = value.replace(",", "");
            value = Number(stringvalue.replace(/[^0-9\.]+/g, ""));

            if (stringvalue.endsWith("k")) {
                value *= 1000;
            } else if (stringvalue.endsWith("m")) {
                value *= 1000000;
            } else if (stringvalue.endsWith("b")) {
                value *= 1000000000;
            }
        }

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Banking Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted banking request.\"`);
            } else {
                generateToast("Banking Request Successfully Sent", `Banking Request ${response["id"]} for ${response["amount"]} has been successfully submitted to the server.`);
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/banking");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'amount_requested': value,
        }));
    });
});

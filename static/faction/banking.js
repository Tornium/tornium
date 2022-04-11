/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

const key = document.currentScript.getAttribute('data-key');

$(document).ready(function() {
    $('#banking-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/faction/userbankingdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 5;

    $("#requestform").submit(function(e) {
        e.preventDefault();
        const xhttp = new XMLHttpRequest();
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

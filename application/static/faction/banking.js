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

const bankingEnabled = document.currentScript.getAttribute("data-banking-enabled");

$(document).ready(function () {
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true,
    });

    $("#banking-table").DataTable({
        processing: true,
        serverSide: true,
        ordering: true,
        responsive: false,
        searching: false,
        ajax: {
            url: "/faction/userbankingdata",
        },
        order: [[2, "desc"]],
        scrollX: true,
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    if (!bankingEnabled) {
        return;
    }

    tfetch("GET", "faction/banking/vault", { errorTitle: "Balance Request Failed" })
        .then((response) => {
            $("#money-balance").text(commas(response["money_balance"]));
            $("#points-balance").text(commas(response["points_balance"]));
        })
        .catch((err) => {
            $("#money-balance").val("ERROR");
            $("#points-balance").val("ERROR");
        });

    $("#request-form").submit(function (e) {
        e.preventDefault();
        let value = $("#request-amount").val();
        value = value.toLowerCase();

        if (value !== "all") {
            const stringValue = value.replace(",", "");
            value = Number(stringValue.replace(/[^0-9\.]+/g, ""));

            if (stringValue.endsWith("k")) {
                value *= 1000;
            } else if (stringValue.endsWith("m")) {
                value *= 1000000;
            } else if (stringValue.endsWith("b")) {
                value *= 1000000000;
            }
        }

        tfetch("POST", "faction/banking", {
            body: { amount_requested: value },
            errorTitle: "Banking Request Failed",
        }).then((response) => {
            generateToast(
                "Banking Request Successfully Sent",
                `Banking Request ${response.id} for ${response.amount} has been successfully submitted to the server.`,
            );
        });
    });
});

/* Copyright (C) 2021-2025 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

const bankingEnabled = document.currentScript.getAttribute("data-banking-enabled");
const factionID = document.currentScript.getAttribute("data-faction-id");

function updateBalance(vaultData) {
    const moneyBalanceSpan = document.getElementById("money-balance");
    const pointsBalanceSpan = document.getElementById("points-balance");

    if (vaultData.error) {
        moneyBalanceSpan.textContent = "ERR";
        pointsBalanceSpan.textContent = "ERR";
    } else {
        moneyBalanceSpan.textContent = commas(vaultData.money_balance);
        pointsBalanceSpan.textContent = commas(vaultData.points_balance);
    }

    moneyBalanceSpan.classList.remove("placeholder");
    pointsBalanceSpan.classList.remove("placeholder");
}

function submitRequest(event) {
    event.preventDefault();

    const requestType = document.querySelector(`input[name="request-type"]:checked`).value;
    const requestAmount = document.getElementById("request-amount").value;
    const requestTimeout = document.getElementById("request-timeout").value;
    const parsedRequestTimeout = requestTimeout == "" ? null : Math.floor(Date.now() / 1000) + parseInt(requestTimeout);

    tfetch("POST", `faction/${factionID}/banking`, {
        body: { type: requestType, amount: requestAmount, timeout: parsedRequestTimeout },
        errorTitle: "Banking Request Failed",
    }).then((response) => {
        generateToast(
            "Banking Request Successfully Sent",
            `Banking Request ${response.id} for ${commas(response.amount)} ${requestType == "points_balance" ? "points" : "money"} has been successfully submitted.`,
        );
    });
}

ready(() => {
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

    tfetch("GET", "faction/banking/vault", { errorTitle: "Balance Request Failed" }).then(updateBalance);

    document.getElementById("request-submit").addEventListener("click", submitRequest);
});

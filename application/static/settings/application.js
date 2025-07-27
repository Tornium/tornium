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

function revokeClient(event) {
    const clientID = this.getAttribute("data-client-id");
    const parent = this.parentNode;

    let xhttp = new XMLHttpRequest();
    xhttp.onload = function () {
        let response = xhttp.response;

        if ("code" in response && response["code"] != "0001") {
            generateToast("Application Revocation Failed", response["message"]);
        } else {
            window.location.reload();
        }
    };

    xhttp.responseType = "json";
    xhttp.open("POST", `/oauth/client/${clientID}/revoke`);
    xhttp.send();
}

ready(() => {
    document.getElementById("revoke-client").addEventListener("click", revokeClient);
});

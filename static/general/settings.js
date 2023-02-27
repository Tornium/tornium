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

const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
});
const token = params.token;

$(document).ready(function() {
    // Theme selection
    const getTheme = function () {
        if (localStorage.getItem('theme')) {
            return localStorage.getItem('theme');
        }

        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'custom-dark' : 'light';
    }

    $("#theme-selector").on("change", function(e) {
        localStorage.setItem("theme", this.value);
        document.documentElement.setAttribute("data-bs-theme", this.value);
    });

    $(`option[value="${getTheme()}"]`).prop("selected", true);

    // TOTP QR code
    $("#show-totp-qr").on("click", function() {
        if(token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        let xhttp = new XMLHttpRequest();

        xhttp.onload = function() {
            let response = xhttp.response;

            if("code" in response) {
                generateToast("QR Code Generation Failed", response["message"]);
                return;
            }

            $("#settings-modal-label").val("TOTP QR Code");
            $("#settings-modal-body").empty();
            $("#settings-modal-body").append($("<p>")).text("You can set up Tornium to use any TOTP provider such as Google Authenticator and Duo Mobile. To set up TOTP, scan the below QR code in an authenticator and follow the provided instructions.");
            $("#settings-modal-body").append($("<div>", {
                "id": "qr-code-container"
            }));

            let qrSuccess = false;
            QRCode.toCanvas($("#qr-code-container"), response["url"], function(e) {
                if(e) {
                    generateToast("QR Code Generation Failed", response["message"]);
                    return;
                }

                qrSuccess = true;
            });

            if(!qrSuccess) {
                return;
            }

            $("#settings-modal-body").append($("<p>")).text(`You can also set up TOTP by manually entering the code into the authenticator app: ${response['secret']}.`);

            let modal = new bootstrap.Modal($("#settings-modal"));
            modal.show();
        }

        xhttp.responseType = "json";
        xhttp.open("GET", `/totp/secret?token=${token}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    });

    // TOTP Regenerate Secret
    $("#regen-totp-secret").on("click", function() {
        if(token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        generateToast("Not Yet Implemented", "TOTP secret regeneration has not yet been fully implemented and tested.", "Warning");
    });

    // TOTP Regenerate Backup Codes
    $("#regen-totp-codes").on("click", function() {
        if(token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        generateToast("Not Yet Implemented", "TOTP backup codes have not yet been fully implemented and tested.", "Warning");
    });
});
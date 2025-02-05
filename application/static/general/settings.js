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

const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
});
const token = params.token;

$(document).ready(function () {
    // Theme selection
    const getTheme = function () {
        if (localStorage.getItem("theme")) {
            return localStorage.getItem("theme");
        }

        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "custom-dark" : "light";
    };

    $("#theme-selector").on("change", function (e) {
        localStorage.setItem("theme", this.value);
        document.documentElement.setAttribute("data-bs-theme", this.value);
    });

    $(`option[value="${getTheme()}"]`).prop("selected", true);

    // Security mode selector
    $("#disable-mfa").on("click", function () {
        if (token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        let xhttp = new XMLHttpRequest();
        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Security Mode Switch Failed", response["message"]);
                window.location.reload();
            } else {
                $("#disable-mfa").attr("disabled", true);
                $("#enable-totp").attr("disabled", false);
                window.location.reload();
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/security?token=${token}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                mode: 0,
            }),
        );
    });

    $("#enable-totp").on("click", function () {
        if (token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        let xhttp = new XMLHttpRequest();
        xhttp.onload = function () {
            let response = xhttp.response;

            if (response.code == 1) {
                $("#disable-mfa").attr("disabled", false);
                $("#enable-totp").attr("disabled", true);

                if (response.details.otp_generated === true) {
                    showTOTP();
                }
            } else if ("code" in response) {
                generateToast("Security Mode Switch Failed", response["message"]);
                window.location.reload();
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/security?token=${token}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(
            JSON.stringify({
                mode: 1,
            }),
        );
    });

    // TOTP QR code
    function showTOTP() {
        if (token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        let xhttp = new XMLHttpRequest();

        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("QR Code Generation Failed", response["message"]);
                return;
            }

            $("#settings-modal-label").text("TOTP QR Code");
            $("#settings-modal-body").empty();
            $("#settings-modal-body").append(
                $("<p>", {
                    text: "You can set up Tornium to use any TOTP provider such as Google Authenticator and Duo Mobile. To set up TOTP, scan the below QR code in an authenticator and follow the provided instructions.",
                }),
            );
            $("#settings-modal-body").append(
                $("<div>", {
                    id: "qr-code-container",
                    class: "d-flex flex-column justify-content-center mx-2",
                }),
            );

            new QRCode(document.getElementById("qr-code-container"), response["url"]);

            $("#settings-modal-body").append(
                $("<p>", {
                    text: `You can also set up TOTP by manually entering the code into the authenticator app: ${response["secret"]}.`,
                }),
            );

            let modal = new bootstrap.Modal($("#settings-modal"));
            modal.show();
        };

        xhttp.responseType = "json";
        xhttp.open("GET", `/totp/secret?token=${token}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    }
    $("#show-totp-qr").on("click", showTOTP);

    // TOTP Regenerate Secret
    $("#regen-totp-secret").on("click", function () {
        if (token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        let xhttp = new XMLHttpRequest();
        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response && response["code"] !== 1) {
                generateToast("TOTP Secret Generation Failed", response["message"]);
            } else {
                generateToast(
                    "TOTP Secret Generation Successful",
                    "The TOTP secret was successfully generated. To add the secret to your authenticator app, " +
                        'press the "Show TOTP QR Code" button.',
                );
            }
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/totp/secret?token=${token}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    });

    // TOTP Regenerate Backup Codes
    $("#regen-totp-codes").on("click", function () {
        if (token === null) {
            generateToast("Permission Denied", "Invalid token", "Error");
            return;
        }

        let xhttp = new XMLHttpRequest();
        xhttp.onload = function () {
            let response = xhttp.response;

            if ("code" in response) {
                generateToast("Backup Generation Failed", response["message"]);
                return;
            }

            $("#settings-modal-label").text("TOTP Backup Codes");
            $("#settings-modal-body").empty();
            $("#settings-modal-body").append(
                $("<p>", {
                    text:
                        "TOTP backup codes are to be used in case your primary authenticator is missing or damaged. " +
                        "Once generated, backup codes are hashed and can never be viewed again so be sure to save them. " +
                        "Once a backup code is used, it is permanently deleted.",
                }),
            );
            $("#settings-modal-body").append(
                $("<ul>", {
                    class: "list-group mb-2",
                    id: "totp-backup-container",
                }),
            );

            $.each(response["codes"], function (index, code) {
                $("#totp-backup-container").append(
                    $("<li>", {
                        class: "list-group-item",
                        text: code,
                    }),
                );
            });

            $("#settings-modal-body").append(
                $("<button>", {
                    class: "btn btn-outline-success m-1",
                    id: "copy-totp-backup",
                    type: "button",
                    text: "Copy",
                }),
            );

            $("#settings-modal-body").append(
                $("<button>", {
                    class: "btn btn-outline-success m-1",
                    id: "save-totp-backup",
                    type: "button",
                    text: "Save as File",
                }),
            );
            $("#save-totp-backup").attr("disabled", true);

            $("#copy-totp-backup").on("click", function () {
                navigator.clipboard.writeText(response["codes"].join("\n")).then(function () {
                    generateToast("Codes Copied", "The TOTP backup codes have been copied to your clipboard");
                });
            });

            $("#save-totp-backup").on("click", function () {
                window.open("data:text/plain;charset=utf-8," + response["codes"].join("\n"));
            });

            let modal = new bootstrap.Modal($("#settings-modal"));
            modal.show();
        };

        xhttp.responseType = "json";
        xhttp.open("POST", `/totp/backup?token=${token}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    });

    function addNewKey() {
        tfetch("POST", "key", { body: { key: $("#api-key-input").val() }, errorTitle: "API Key Add Failed" }).then(
            () => {
                generateToast("API Key Input Successful", "The Tornium API server has successfully set your API key.");
                window.location.reload();
            },
        );
    }

    $("#api-key-input").on("keypress", function (e) {
        if (e.which === 13) {
            addNewKey();
        }
    });
    $("#submit-new-key").on("click", addNewKey);

    $(".disable-key").on("click", function () {
        tfetch("PATCH", `key/${$(this).attr("data-key-guid")}`, {
            body: { disabled: true },
            errorTitle: "API Key Disable Failed",
        }).then(() => {
            window.location.reload();
        });
    });

    $(".enable-key").on("click", function () {
        tfetch("PATCH", `key/${$(this).attr("data-key-guid")}`, {
            body: { disabled: false },
            errorTitle: "API Key Enable Failed",
        }).then(() => {
            window.location.reload();
        });
    });

    $(".delete-key").on("click", function () {
        tfetch("DELETE", `key/${$(this).attr("data-key-guid")}`, { errorTitle: "API Key Delete Failed" }).then(() => {
            generateToast("API Key Delete Successful");
            $(this).closest(".key-parent").remove();
        });
    });
});

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

function toggleSetting(settingID, settingValue) {
    tfetch("PUT", `user/settings/${settingID}`, {
        body: {
            enabled: settingValue,
        },
        errorTitle: "Setting Toggle Failed",
        errorHandler: (jsonError) => {
            // TODO: Update error handler
            console.log(jsonError);
        },
    }).then((data) => {
        generateToast("Setting Toggle Successful", `The setting ${settingID} has been successfully toggled.`);
    });
}

function revokeClient(event) {
    const clientID = this.getAttribute("data-client-id");
    const parent = this.parentNode;

    let xhttp = new XMLHttpRequest();
    xhttp.onload = function () {
        let response = xhttp.response;

        if ("code" in response && response["code"] != "0001") {
            generateToast("Application Revocation Failed", response["message"]);
            window.location.reload();
        } else {
            parent.remove();
            generateToast("Application Revocation Successful", "The application was successully revoked.");

            const applicationCountElement = document.getElementById("application-count");
            const applicationCount = parseInt(applicationCountElement.textContent);
            applicationCountElement.textContent = applicationCount - 1;
        }
    };

    xhttp.responseType = "json";
    xhttp.open("POST", `/oauth/client/${clientID}/revoke`);
    xhttp.send();
}

ready(() => {
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

    document.getElementById("cpr-toggle-enable").addEventListener("click", (event) => {
        toggleSetting("cpr", true);
    });
    document.getElementById("cpr-toggle-disable").addEventListener("click", (event) => {
        toggleSetting("cpr", false);
    });

    document.getElementById("stat-db-toggle-enable").addEventListener("click", (event) => {
        toggleSetting("stat-db", true);
    });
    document.getElementById("stat-db-toggle-disable").addEventListener("click", (event) => {
        toggleSetting("stat-db", false);
    });

    Array.from(document.getElementsByClassName("revoke-client")).forEach((button) => {
        button.addEventListener("click", revokeClient);
    });
});

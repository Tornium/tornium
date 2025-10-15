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

const clientID = document.currentScript.getAttribute("data-client-id");

function regenerateClientSecret(event) {
    _tfetch("POST", `/developers/clients/${clientID}/regenerate-secret`, {
        errorTitle: "Secret Regeneration Failed",
    }).then((clientData) => {
        const clientSecretOutput = document.getElementById("client-secret");
        clientSecretOutput.classList.remove("d-none");
        clientSecretOutput.classList.add("mb-2");
        clientSecretOutput.value = clientData.client_secret;
    });
}

ready(() => {
    document.getElementById("regenerate-client-secret").addEventListener("click", regenerateClientSecret);
});

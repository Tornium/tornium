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

function createDeleteConfirmation(event) {
    const confirmation = document.createElement("alert-confirm");
    confirmation.setAttribute("data-title", "Are you sure?");
    confirmation.setAttribute(
        "data-body-text",
        "This action cannot be undone. This OAuth application will be permanently deleted from our servers.",
    );
    confirmation.setAttribute("data-close-button-text", "Cancel");
    confirmation.setAttribute("data-accept-button-text", "Delete");
    confirmation.setAttribute("data-close-callback", null);
    confirmation.setAttribute("data-accept-callback", "deleteClient");
    document.body.appendChild(confirmation);
}

function deleteClient(event) {
    _tfetch("DELETE", `/developers/clients/${clientID}`, {
        errorTitle: "OAuth Client Deletion Failed",
    }).then(() => {
        window.location.href = "/developers/clients";
    });
}

ready(() => {
    const regenerateClientSecretButton = document.getElementById("regenerate-client-secret");

    if (regenerateClientSecretButton != null) {
        regenerateClientSecretButton.addEventListener("click", regenerateClientSecret);
    }

    document.getElementById("delete-client").addEventListener("click", createDeleteConfirmation);
});

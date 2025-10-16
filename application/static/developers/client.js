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

function createNewClientRedirectURI(event) {
    const defaultItem = document.getElementById("client-redirect-uri-default");
    if (!defaultItem.classList.contains("d-none")) {
        defaultItem.classList.add("d-none");
    }

    const newURIItem = document.createElement("li");
    newURIItem.classList.add("list-group-item", "d-flex", "justify-content-around", "align-items-center");

    const newURIInput = document.createElement("input");
    newURIInput.setAttribute("type", "url");
    newURIInput.classList.add("form-control", "w-100", "me-2");
    newURIItem.append(newURIInput);

    const newURIButton = document.createElement("button");
    newURIButton.setAttribute("type", "button");
    newURIButton.classList.add("btn", "btn-sm", "btn-outline-danger", "remove-client-redirect-uri");
    newURIButton.innerHTML = `<i class="fa-solid fa-trash"></i>`;
    newURIButton.addEventListener("click", removeClientRedirectButton);
    newURIItem.append(newURIButton);

    const clientRedirectURIList = document.getElementById("client-redirect-uri");
    clientRedirectURIList.append(newURIItem);
}

function removeClientRedirectButton(event) {
    const clientRedirectURIItem = this.parentNode;
    clientRedirectURIItem.remove();

    const clientRedirectURIList = document.getElementById("client-redirect-uri");

    if (clientRedirectURIList.childElementCount == 1) {
        const defaultItem = document.getElementById("client-redirect-uri-default");
        defaultItem.classList.remove("d-none");
    }
}

ready(() => {
    const regenerateClientSecretButton = document.getElementById("regenerate-client-secret");

    if (regenerateClientSecretButton != null) {
        regenerateClientSecretButton.addEventListener("click", regenerateClientSecret);
    }

    document.getElementById("delete-client").addEventListener("click", createDeleteConfirmation);
    document.getElementById("client-redirect-uri-new").addEventListener("click", createNewClientRedirectURI);

    Array.from(document.getElementsByClassName("remove-client-redirect-uri")).forEach((removeClientRedirectButton) => {
        removeClientRedirectButton.addEventListener("click", removeClientRedirectButton);
    });
});

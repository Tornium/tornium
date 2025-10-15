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

function createNewClient(event) {
    const clientNameInput = document.getElementById("client-name");
    const clientTypeInput = document.querySelector(`input[name="client-type-selector"]:checked`);

    if (clientNameInput.value == "") {
        generateToast("Invalid Client Name", "The client name must have a non-empty value.");
        return;
    } else if (clientTypeInput == null || clientTypeInput.value == null || clientTypeInput.value == "on") {
        generateToast("Invalid Client Type", "A client type must be selected.");
        return;
    }

    _tfetch("POST", `/developers/clients/new`, {
        body: {
            client_name: clientNameInput.value,
            client_type: clientTypeInput.value,
        },
        errorTitle: "Failed to Create Client",
    }).then((clientData) => {
        window.location.href = `/developers/clients/${clientData.client_id}`;
    });
}

ready(() => {
    document.getElementById("create-oauth-client").addEventListener("click", createNewClient);
});

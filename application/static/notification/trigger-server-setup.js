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

const trigger_id = document.currentScript.getAttribute("data-trigger-id");

let channelInput;
let resourceIDInput;

function notificationTypeConvert(typeString) {
    switch (typeString) {
        case "notification-type-one-shot":
            return true;
        case "notification-type-repeating":
            return false;
        default:
            throw new Error(`Illegal message type string: ${typeString}`);
    }
}

function setupTrigger(event) {
    const resource_id = parseInt(resourceIDInput.value);
    const channel_id = channelInput.options[channelInput.selectedIndex].value;
    let triggerMessageType;

    try {
        triggerMessageType = notificationTypeConvert(document.querySelector("input[name=notification-type]:checked").id);
    } catch (TypeError) {
        generateToast("Invalid message type", "A message type must be selected.", "warning");
        return;
    }

    let parameters = {}

    for (let parameterInput of document.querySelectorAll(".parameter-value")) {
        parameters[parameterInput.getAttribute("data-parameter")] = parameterInput.value;
    }

    if (typeof resource_id != "number") {
        generateToast("Invalid resource ID", "The resource ID must be an integer.", "warning");
        return;
    }

    tfetch("POST", `notification/trigger/${trigger_id}/guild/${guildid}`, {
        body: {
            channel_id: channel_id,
            resource_id: resource_id,
            one_shot: triggerMessageType,
            parameters: parameters,
        },
        errorTitle: "Notification Creation Failed",
        errorHandler: (jsonError) => {
            console.log(jsonError);
        }
    }).then((data) => {
        console.log(data);
        window.location.href = `/bot/dashboard/${guildid}/notification`;
    });
}

ready(() => {
    let channelsPromise = channelsRequest();

    channelInput = document.getElementById("notification-channel");
    resourceIDInput = document.getElementById("notification-resource-id");

    channelsPromise.then(() => {
        new TomSelect(".discord-channel-selector", {
            create: false,
        });
    })

    document.getElementById("setup-trigger").addEventListener("click", setupTrigger);
});

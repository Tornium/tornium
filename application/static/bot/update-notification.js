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

const channel_id = document.currentScript.getAttribute("data-channel-id");
const trigger_id = document.currentScript.getAttribute("data-trigger-id");
const notification_id = document.currentScript.getAttribute("data-notification-id");

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
        triggerMessageType = notificationTypeConvert(
            document.querySelector("input[name=notification-type]:checked").id,
        );
    } catch (TypeError) {
        generateToast("Invalid message type", "A message type must be selected.", "warning");
        return;
    }

    let parameters = {};

    for (let parameterInput of document.querySelectorAll(".parameter-value")) {
        parameters[parameterInput.getAttribute("data-parameter")] = parameterInput.value;
    }

    if (typeof resource_id != "number") {
        generateToast("Invalid resource ID", "The resource ID must be an integer.", "warning");
        return;
    } else if (resource_id == 0) {
        generateToast("Invalid resource ID", "The resource ID must not be 0.", "warning");
        return;
    }

    tfetch("PUT", `notification/${notification_id}`, {
        body: {
            channel_id: channel_id,
            resource_id: resource_id,
            one_shot: triggerMessageType,
            parameters: parameters,
        },
        errorTitle: "Notification Update Failed",
        errorHandler: (jsonError) => {
            // TODO: Update error handler
            console.log(jsonError);
        },
    }).then((data) => {
        window.location.href = `/bot/dashboard/${guildid}/notification`;
    });
}

function deleteNotification(event) {
    tfetch("DELETE", `notification/${notification_id}`, {
        errorTitle: "Notification Delete Failed",
        errorHandler: (jsonError) => {
            // TODO: Update error handler
            console.log(jsonError);
        },
    }).then((data) => {
        window.location.href = `/bot/dashboard/${guildid}/notification`;
    });
}

function toggleNotification(event) {
    console.log(event.target.id);
    let enable = null;

    if (event.target.id == "notification-toggle-enable") {
        enable = true;
    } else if (event.target.id == "notification-toggle-disable") {
        enable = false;
    } else {
        return;
    }

    tfetch("POST", `notification/${notification_id}/toggle`, {
        body: {
            enabled: enable,
        },
        errorTitle: "Notification Toggle Failed",
        errorHandler: (jsonError) => {
            // TODO: Update error handler
            console.log(jsonError);
        },
    }).then((data) => {
        generateToast("Notification Toggled", "The notification has been successfully toggled.");
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

        const channelOption = $(`#notification-channel option[value="${channel_id}"]`);
        if (channelOption.length !== 0) {
            channelOption.attr("selected", "");
        }
    });

    document.getElementById("setup-trigger").addEventListener("click", setupTrigger);
    document.getElementById("delete-notification").addEventListener("click", deleteNotification);
    document.getElementById("notification-toggle-enable").addEventListener("click", toggleNotification);
    document.getElementById("notification-toggle-disable").addEventListener("click", toggleNotification);
});

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

window.notificationErrorCallback = function(jsonError, container) {
    const errorNode = document.createElement("span");
    errorNode.textContent = " Data failed to load...";

    const errorIcon = document.createElement("i");
    errorIcon.classList.add("fa-solid", "fa-skull-crossbones");

    container.innerHTML = "";
    container.appendChild(errorIcon);
    container.appendChild(errorNode);
}

window.addNotificationToViewer = function(notification, notificationContainer) {
    const notificationNode = document.createElement("div");
    notificationNode.classList.add("card", "mx-2", "mt-2", "viewer-card");
    notificationNode.setAttribute("data-notification-id", notification.nid);
    notificationContainer.append(notificationNode);

    const notificationRow = document.createElement("div");
    notificationRow.classList.add("row", "p-2", "align-middle");
    notificationNode.append(notificationRow);

    const notificationNameElement = document.createElement("div");
    notificationNameElement.classList.add("col-sm-12", "col-md-6", "col-xl-4");
    notificationNameElement.textContent = notification.trigger.name;
    notificationRow.append(notificationNameElement);

    const notificationResourceElement = document.createElement("div");
    notificationResourceElement.classList.add("col-sm-12", "col-md-4", "cl-xl-2");
    notificationResourceElement.textContent = `${notification.trigger.resource}: ${notification.resource_id}`;
    notificationRow.append(notificationResourceElement);

    const notificationPaddingElement = document.createElement("div");
    notificationPaddingElement.classList.add("col-sm-0", "col-md-0", "col-xl-2");
    notificationRow.append(notificationPaddingElement);

    const notificationActionsContainer = document.createElement("div");
    notificationActionsContainer.classList.add("col-sm-12", "col-md-2", "col-xl-2");
    notificationRow.append(notificationActionsContainer);
    
    const notificationActions = document.createElement("div");
    notificationActions.classList.add("w-100", "justify-content-end", "d-flex");
    notificationActionsContainer.append(notificationActions);

    const viewAction = document.createElement("a")
    viewAction.classList.add("btn", "btn-sm", "btn-outline-secondary", "me-2");
    viewAction.href = `/bot/dashboard/${guildid}/notification/${notification.nid}`;
    notificationActions.append(viewAction);

    const viewActionIcon = document.createElement("i");
    viewActionIcon.classList.add("fa-regular", "fa-eye");
    viewAction.append(viewActionIcon);
}

function load_channels([notificationConfig, channels]) {
    let notificationsLogChannel = $(`#notifications-log-channel option[value="${notificationConfig["log_channel"]}"]`);

    if (notificationsLogChannel.length !== 0) {
        notificationsLogChannel.attr("selected", "");
    }
}

function handle_notification_global_toggle(event) {
    console.log(event);
    let enabled;

    if (event.target.id == "notification-toggle-enable") {
        enabled = true;
    } else if (event.target.id == "notification-toggle-disable") {
        enabled = false;
    } else {
        generateToast("Update Notification Toggle Failed", "Invalid event target ID", "error");
        throw new Error(`Illegal event target ID: ${event.target.id}`);
    }

    tfetch("PUT", `bot/${guildid}/notification`, {
        body: {enabled: enabled},
        errorTitle: "Notifications Toggle Failed",
        errorHandler: () => {
            // TODO: Switch the state of the toggle to the original state (and possibly suppress the change event)
        },
    }).then(() => {
        generateToast("Notifications Toggle Successful", "The server's notifications were successfully toggled", "info");
    });
}

function change_notification_log_channel(event) {
    tfetch("PUT", `bot/${guildid}/notification/log-channel`, {
        body: { channel_id: this.options[this.selectedIndex].value },
        errorTitle: "Notifications Log Channel Set Failed",
        errorHandler: () => {
            // TODO: Switch the state of the toggle to the original state (and possibly suppress the change event)
        }
    }).then(() => {
        generateToast("Notifications Log Channel Set Successful", "The server's notification log channel was successfully set", "info");
    });
}

ready(() => {
    const notificationConfigPromise = tfetch("GET", `bot/${guildid}/notification`, { errorTitle: "Server Notifications Config Failed to Load" });
    const channelsPromise = channelsRequest();

    Promise.all([notificationConfigPromise, channelsPromise]).then((configs) => load_channels(configs)).finally(() => {
            document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    document.querySelectorAll("input[name=notification-toggle]").forEach((button) => {button.addEventListener("change", handle_notification_global_toggle)});
    document.getElementById("notifications-log-channel").addEventListener("change", change_notification_log_channel);
});

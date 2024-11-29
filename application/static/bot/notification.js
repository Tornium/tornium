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

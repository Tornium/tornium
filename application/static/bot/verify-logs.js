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

const error_types = {
    unverified: "Not Verified",
    discord_permission: "Discord Permissions Issue",
    no_api_key: "No API Key",
    config: "Bot Config Issue",
    torn_api: "Torn API Error",
    discord_api: "Discord API Error",
};

function showDetails(event) {
    const defaultDetailsMessage = document.getElementById("default-details-message");
    const detailsGroup = document.getElementById("verification-details-group");
    const logsTable = document.getElementById("verification-logs-viewer");

    const logNode = event.target.closest(".viewer-card[data-log-id]");
    const logGUID = logNode.getAttribute("data-log-id");
    const log = logsTable.getData().find((log) => log.guid == logGUID);

    if (detailsGroup == null || logsTable == null || log == null) {
        return;
    }

    document.getElementById("details-timestamp").textContent = tcttime(log.timestamp);
    document.getElementById("details-discord").textContent = log.discord_id || "N/A";
    document.getElementById("details-user").textContent =
        log.user == null ? "N/A" : `${log.user.name} [${log.user.id}]`;
    document
        .getElementById("details-user")
        .setAttribute("href", log.user == null ? "#" : `https://www.torn.com/profiles.php?XID=${log.user.id}`);

    const isSuccess = log.error_type == null;
    if (isSuccess) {
        document.getElementById("details-status").textContent = "Success";

        const [oldNickname, newNickname] = log.success.nickname;
        if (oldNickname != null && oldNickname != newNickname) {
            document.getElementById("details-old-nickname").textContent = oldNickname;
            document.getElementById("details-new-nickname").textContent = newNickname;
        }

        // TODO: Format the roles well
        document.getElementById("details-roles-added").textContent = log.success.roles_added.join("\n") || "None";
        document.getElementById("details-roles-removed").textContent = log.success.roles_removed.join("\n") || "None";
    } else {
        document.getElementById("details-status").textContent = "Failed";
        document.getElementById("details-error-type").textContent = error_types[log.failure.error_type] || "Unknown";
        document.getElementById("details-error-code").textContent = log.failure.error_code || "N/A";
        document.getElementById("details-error-message").textContent = log.failure.error_message || "N/A";
    }

    detailsGroup.classList.remove("d-none");
    detailsGroup.classList.toggle("is-success", isSuccess);
    detailsGroup.classList.toggle("is-failure", !isSuccess);
    defaultDetailsMessage.classList.add("d-none");
}

window.viewerErrorCallback = function (jsonError, container) {
    const errorNode = document.createElement("span");
    errorNode.textContent = " Data failed to load...";

    const errorIcon = document.createElement("i");
    errorIcon.classList.add("fa-solid", "fa-skull-crossbones");

    container.innerHTML = "";
    container.appendChild(errorIcon);
    container.appendChild(errorNode);
};

window.addVerificationLogToViewer = function (log, logContainer) {
    let logChanges = [];
    let logResult = "Unknown";

    if (log.success != null) {
        logResult = "Success";

        if (log.success.nickname[0] != log.success.nickname[1]) {
            logChanges.push("nickname");
        }
        if (log.success.roles_added.length != 0) {
            logChanges.push(`+${log.success.roles_added.length} roles`);
        }
        if (log.success.roles_removed.length != 0) {
            logChanges.push(`-${log.success.roles_removed.length} roles`);
        }
    } else if (log.failure != null) {
        logResult = "Failed";
        logChanges = [error_types[log.failure.error_type] || "Unknown"];
    } else {
        logResult = "Unknown";
        logChanges = ["N/A"];
    }

    logChanges = logChanges.join(", ");

    const logNode = document.createElement("div");
    logNode.classList.add("card", "mx-2", "mt-2", "viewer-card");
    logNode.setAttribute("data-log-id", log.guid);
    logContainer.append(logNode);

    const logRow = document.createElement("div");
    logRow.classList.add("row", "p-2", "align-middle");
    logNode.append(logRow);

    const logUserElement = document.createElement("a");
    logUserElement.classList.add("col-sm-12", "col-md-3");
    logUserElement.textContent = `${log.user.name} [${log.user.id}]`;
    logUserElement.setAttribute("href", `https://www.torn.com/profiles.php?XID=${log.user.id}`);
    logRow.append(logUserElement);

    const logResultElement = document.createElement("div");
    logResultElement.classList.add("col-sm-12", "col-md-2");
    logResultElement.textContent = logResult;
    logRow.append(logResultElement);

    const logChangesElement = document.createElement("div");
    logChangesElement.classList.add("col-sm-12", "col-md-4", "text-truncate");
    logChangesElement.textContent = logChanges;
    logRow.append(logChangesElement);

    const logDateTimeElement = document.createElement("time");
    logDateTimeElement.classList.add("col-sm-12", "col-md-2");
    logDateTimeElement.setAttribute("datetime", new Date(log.timestamp).toISOString());
    logDateTimeElement.textContent = reltime(log.timestamp);
    logRow.append(logDateTimeElement);

    const logActionsContainer = document.createElement("div");
    logActionsContainer.classList.add("col-sm-12", "col-md-1", "mt-2", "mt-md-0");
    logRow.append(logActionsContainer);

    const logActions = document.createElement("div");
    logActions.classList.add("w-100", "justify-content-end", "d-flex");
    logActionsContainer.append(logActions);

    const viewAction = document.createElement("button");
    viewAction.classList.add("btn", "btn-sm", "btn-outline-secondary", "me-2");
    viewAction.addEventListener("click", showDetails);
    logActions.append(viewAction);

    const viewActionIcon = document.createElement("i");
    viewActionIcon.classList.add("fa-regular", "fa-eye");
    viewAction.append(viewActionIcon);
};

window.filterTomSelectMultiple = function (element) {
    return Array.from(element.selectedOptions).map(({ value }) => value);
};

ready(() => {
    document.querySelectorAll(".automatic-tom-select").forEach((element) => {
        new TomSelect(element, {
            create: false,
            maxOptions: null,
            onItemAdd: tomselectClearAfterAdd,
        });
    });
});

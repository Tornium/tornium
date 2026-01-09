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

window.viewerErrorCallback = function (jsonError, container) {
    const errorNode = document.createElement("span");
    errorNode.textContent = " Data failed to load...";

    const errorIcon = document.createElement("i");
    errorIcon.classList.add("fa-solid", "fa-skull-crossbones");

    container.innerHTML = "";
    container.appendChild(errorIcon);
    container.appendChild(errorNode);
};

function itemToString(item, quantity = null) {
    quantity = quantity == null ? item.quantity : quantity;

    if (item.id != null) {
        return `${commas(quantity)}x ${item.name}`;
    } else if (item.is_nerve_refill) {
        return `${commas(quantity)}x nerve refill`;
    } else if (item.is_energy_refill) {
        return `${commas(quantity)}x energy refill`;
    } else {
        return "Unknown";
    }
}

window.addUsageLogToViewer = function (log, logContainer) {
    const logNode = document.createElement("div");
    logNode.classList.add("card", "mx-2", "mt-2", "viewer-card");
    logNode.setAttribute("data-log-id", log.id);
    logContainer.append(logNode);

    const logRow = document.createElement("div");
    logRow.classList.add("row", "p-2", "align-middle");
    logNode.append(logRow);

    const logNameElement = document.createElement("div");
    logNameElement.classList.add("col-sm-12", "col-md-4");
    logNameElement.textContent = `${log.user.name} [${log.user.id}]`;
    logRow.append(logNameElement);

    const logActionElement = document.createElement("div");
    logActionElement.classList.add("col-sm-12", "col-md-2");
    logActionElement.textContent = log.action;
    logRow.append(logActionElement);

    const logItemElement = document.createElement("div");
    logItemElement.classList.add("col-sm-12", "col-md-3", "text-truncate");
    logItemElement.textContent = itemToString(log.item);
    logRow.append(logItemElement);

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

    const viewAction = document.createElement("a");
    viewAction.classList.add("btn", "btn-sm", "btn-outline-secondary", "me-2");
    viewAction.href = `https://www.torn.com/factions.php?step=your&search=${log.user.name}&from=${log.timestamp - 1}&to=${log.timestamp + 1}`;
    logActions.append(viewAction);

    const viewActionIcon = document.createElement("i");
    viewActionIcon.classList.add("fa-regular", "fa-eye");
    viewAction.append(viewActionIcon);
};

window.addCumulativeToViewer = function (group, groupContainer) {
    const groupNode = document.createElement("div");
    groupNode.classList.add("card", "mx-2", "mt-2", "viewer-card");
    groupContainer.append(groupNode);

    const groupRow = document.createElement("div");
    groupRow.classList.add("row", "p-2", "align-middle");
    groupNode.append(groupRow);

    const groupNameElement = document.createElement("div");
    groupNameElement.classList.add("col-sm-12", "col-md-4");
    groupNameElement.textContent = `${group.user.name} [${group.user.id}]`;
    groupRow.append(groupNameElement);

    const groupActionElement = document.createElement("div");
    groupActionElement.classList.add("col-sm-12", "col-md-2");
    groupActionElement.textContent = group.action;
    groupRow.append(groupActionElement);

    const groupItemElement = document.createElement("div");
    groupItemElement.classList.add("col-sm-12", "col-md-3", "text-truncate");
    groupItemElement.textContent = itemToString(group.item, group.cumulative_quantity);
    groupRow.append(groupItemElement);

    const groupActionsContainer = document.createElement("div");
    groupActionsContainer.classList.add("col-sm-12", "col-md-1", "mt-2", "mt-md-0");
    groupRow.append(groupActionsContainer);

    const groupActions = document.createElement("div");
    groupActions.classList.add("w-100", "justify-content-end", "d-flex");
    groupActionsContainer.append(groupActions);
};

window.filterTomSelectMultiple = function (element) {
    return Array.from(element.selectedOptions).map(({ value }) => value);
};

ready(() => {
    document.querySelectorAll(".automatic-tom-select").forEach((element) => {
        new TomSelect(element, {
            create: false,
            maxOptions: null,
        });
    });
    itemsRequest().finally(() => {
        document.querySelectorAll(".item-selector").forEach((element) => {
            new TomSelect(element, {
                create: false,
            });
        });
    });
});

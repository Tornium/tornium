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

window.addOverdoseEventToViewer = function (event, eventContainer) {
    const eventNode = document.createElement("div");
    eventNode.classList.add("card", "mx-2", "mt-2", "viewer-card");
    eventNode.setAttribute("data-event-id", event.id);
    eventContainer.append(eventNode);

    const eventRow = document.createElement("div");
    eventRow.classList.add("row", "p-2", "align-middle");
    eventNode.append(eventRow);

    const eventNameElement = document.createElement("div");
    eventNameElement.classList.add("col-sm-12", "col-md-4");
    eventNameElement.textContent = `${event.user.name} [${event.user.id}]`;
    eventRow.append(eventNameElement);

    const eventActionElement = document.createElement("div");
    eventActionElement.classList.add("col-sm-12", "col-md-2");
    eventActionElement.textContent = event.action;
    eventRow.append(eventActionElement);

    const eventItemElement = document.createElement("div");
    eventItemElement.classList.add("col-sm-12", "col-md-3", "text-truncate");
    eventItemElement.textContent = event.drug == null ? "Unknown Drug" : event.drug.name;
    eventRow.append(eventItemElement);

    const eventDateTimeElement = document.createElement("time");
    eventDateTimeElement.classList.add("col-sm-12", "col-md-2");
    eventDateTimeElement.setAttribute("datetime", new Date(event.timestamp).toISOString());
    eventDateTimeElement.textContent = reltime(event.timestamp);
    eventRow.append(eventDateTimeElement);
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
    itemsRequest().finally(() => {
        document.querySelectorAll(".item-selector").forEach((element) => {
            new TomSelect(element, {
                create: false,
                onItemAdd: tomselectClearAfterAdd,
            });
        });
    });
});

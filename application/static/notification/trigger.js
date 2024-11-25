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

window.triggerErrorCallback = function(jsonError, container) {
    const errorNode = document.createElement("span");
    errorNode.textContent = " Data failed to load...";

    const errorIcon = document.createElement("i");
    errorIcon.classList.add("fa-solid", "fa-skull-crossbones");

    container.innerHTML = "";
    container.appendChild(errorIcon);
    container.appendChild(errorNode);
}

window.addTriggerToViewer = function(trigger, triggerContainer) {
    const triggerNode = document.createElement("div");
    triggerNode.classList.add("card", "mx-2", "mt-2", "viewer-card");
    triggerNode.setAttribute("data-trigger-id", trigger.tid);
    triggerContainer.append(triggerNode);

    const triggerRow = document.createElement("div");
    triggerRow.classList.add("row", "p-2", "align-middle");
    triggerNode.append(triggerRow);

    const triggerNameElement = document.createElement("div");
    triggerNameElement.classList.add("col-sm-12", "col-md-2", "col-xl-2");
    triggerNameElement.textContent = trigger.name;
    triggerRow.append(triggerNameElement);

    const triggerDescriptionElement = document.createElement("div");
    triggerDescriptionElement.classList.add("col-sm-12", "col-md-4", "col-xl-2", "text-truncate");
    triggerDescriptionElement.textContent = trigger.description;
    triggerRow.append(triggerDescriptionElement);

    const triggerPaddingElement = document.createElement("div");
    triggerPaddingElement.classList.add("col-sm-0", "col-md-4", "col-xl-6");
    triggerRow.append(triggerPaddingElement);

    const triggerActionsContainer = document.createElement("div");
    triggerActionsContainer.classList.add("col-sm-12", "col-md-2", "col-xl-2");
    triggerRow.append(triggerActionsContainer);
    
    const triggerActions = document.createElement("div");
    triggerActions.classList.add("w-100", "justify-content-end", "d-flex");
    triggerActionsContainer.append(triggerActions);

    const viewAction = document.createElement("a")
    viewAction.classList.add("btn", "btn-sm", "btn-outline-secondary", "me-2");
    viewAction.href = `/notification/trigger/${trigger.tid}`;
    triggerActions.append(viewAction);

    const viewActionIcon = document.createElement("i");
    viewActionIcon.classList.add("fa-regular", "fa-eye");
    viewAction.append(viewActionIcon);
}

let viewerPage = 0;
const viewerLimit = 10;

const triggerNextPage = document.getElementById("trigger-next-page");
const triggerPreviousPage = document.getElementById("trigger-previous-page");


function loadTriggers(triggerContainer, triggerCountContainer) {
    return;
    const offset = Math.max(viewerPage * viewerLimit - 1, 0);

    tfetch("GET", `notification/trigger?offset=${offset}&limit=${viewerLimit}`, {
        errorTitle: "Notification Trigger Fetch Failed",
        errorHandler: (jsonError) => {
        }
    }).then((data) => {
        const triggerCount = data.count;
        triggerContainer.replaceChildren();

        if (triggerCount == 0) {
            triggerContainer.textContent = "No results found...";
            triggerCountContainer.textContent = "No";
            return;
        }

        triggerCountContainer.textContent = commas(triggerCount);

        for (const trigger of data.triggers) {
            addTriggerToViewer(triggerContainer, trigger);
        }

        if (viewerPage == 0) {
            triggerPreviousPage.setAttribute("disabled", "disabled");
        }

        if (data.triggers.length != viewerLimit) {
            triggerNextPage.setAttribute("disabled", "disabled");
        }

        if (viewerPage != 0 && data.triggers.length == viewerLimit) {
            triggerPreviousPage.setAttribute("disabled", "");
            triggerNextPage.setAttribute("disabled", "");
        }
    });
}

ready(() => {
    const triggerContainer = document.getElementById("existing-trigger-container");
    const triggerCountContainer = document.getElementById("trigger-count");

    function changeViewerPage(direction) {
        viewerPage = viewerPage + direction;
        loadTriggers(triggerContainer, triggerCountContainer);
    }

    loadTriggers(triggerContainer, triggerCountContainer);

    triggerNextPage.addEventListener("click", () => {changeViewerPage(1)});
    triggerPreviousPage.addEventListener("click", () => {changeViewerPage(-1)});
});

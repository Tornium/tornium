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
    triggerDescriptionElement.classList.add("col-sm-12", "col-md-8", "col-xl-6", "text-truncate");
    triggerDescriptionElement.textContent = trigger.description;
    triggerRow.append(triggerDescriptionElement);

    const triggerPaddingElement = document.createElement("div");
    triggerPaddingElement.classList.add("col-sm-0", "col-md-0", "col-xl-2");
    triggerRow.append(triggerPaddingElement);

    const triggerActionsContainer = document.createElement("div");
    triggerActionsContainer.classList.add("col-sm-12", "col-md-2", "col-xl-2");
    triggerRow.append(triggerActionsContainer);
    
    const triggerActions = document.createElement("div");
    triggerActions.classList.add("w-100", "justify-content-end", "d-flex");
    triggerActionsContainer.append(triggerActions);

    const viewAction = document.createElement("a")
    viewAction.classList.add("btn", "btn-sm", "btn-outline-secondary", "me-2");
    viewAction.href = `/notification/trigger/view/${trigger.tid}`;
    triggerActions.append(viewAction);

    const viewActionIcon = document.createElement("i");
    viewActionIcon.classList.add("fa-regular", "fa-eye");
    viewAction.append(viewActionIcon);
}

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

class DynamicList extends HTMLElement {
    constructor() {
        super();

        this.listContainer = null;
        this.rowCount = -1;
    }

    connectedCallback() {
        this.initializeDOM();
    }

    initializeDOM() {
        const card = document.createElement("div");
        card.classList.add("card");
        this.append(card);

        const header = document.createElement("div");
        header.classList.add("card-header");
        header.innerHTML = this.getAttribute("data-header");
        card.append(header);

        this.listContainer = document.createElement("ul");
        this.listContainer.classList.add("list-group", "list-group-flush");
        card.append(this.listContainer);

        const footer = document.createElement("div");
        footer.classList.add("card-footer");
        card.append(footer);

        const newButton = document.createElement("button");
        newButton.classList.add("btn", "btn-outline-success");
        newButton.textContent = this.getAttribute("data-button-text");
        newButton.addEventListener("click", (event) => this.addNewRow(event));
        footer.append(newButton);
    }

    addNewRow(event) {
        this.rowCount++;
        const rowID = this.rowCount;

        const listElement = document.createElement("li");
        listElement.classList.add("list-group-item", "dynamic-list-row");
        this.listContainer.append(listElement);

        const rowContainer = document.createElement("div");
        rowContainer.classList.add("row");
        listElement.append(rowContainer);

        const nameContainer = document.createElement("div");
        nameContainer.classList.add("col-sm-12", "col-md-5", "mb-3", "mb-md-0", "p-1", "form-floating");
        rowContainer.append(nameContainer);

        const nameInput = document.createElement("input");
        nameInput.setAttribute("type", "text");
        nameInput.setAttribute("placeholder", "");
        nameInput.classList.add("form-control", "dynamic-list-key");
        nameInput.id = `dynamic-list-key-${rowID}`;
        nameContainer.append(nameInput);

        const nameLabel = document.createElement("label");
        nameLabel.setAttribute("for", `dynamic-list-key-${rowID}`);
        nameLabel.textContent = "Name";
        nameContainer.append(nameLabel);

        const descriptionContainer = document.createElement("div");
        descriptionContainer.classList.add("col-sm-12", "col-md-5", "mb-3", "mb-md-0", "p-1", "form-floating");
        rowContainer.append(descriptionContainer);

        const descriptionInput = document.createElement("input");
        descriptionInput.setAttribute("type", "text");
        descriptionInput.setAttribute("placeholder", "");
        descriptionInput.classList.add("form-control", "dynamic-list-value");
        descriptionInput.id = `dynamic-list-value-${rowID}`;
        descriptionContainer.append(descriptionInput);

        const descriptionLabel = document.createElement("label");
        descriptionLabel.setAttribute("for", `dynamic-list-value-${rowID}`);
        descriptionLabel.textContent = "Description";
        descriptionContainer.append(descriptionLabel);

        const buttonContainer = document.createElement("div");
        buttonContainer.classList.add("col-sm-12", "col-md-2", "mb-3", "mb-md-0", "d-flex", "align-items-center", "justify-content-end");
        rowContainer.append(buttonContainer);

        const deleteButton = document.createElement("button");
        deleteButton.classList.add("btn", "btn-outline-danger");
        deleteButton.innerHTML = "<i class=\"fa-solid fa-trash\"></i>";
        deleteButton.addEventListener("click", (event) => this.deleteRow(event));
        buttonContainer.append(deleteButton);
    }

    deleteRow(event) {
        const deleteButton = event.target;
        const rowContainer = deleteButton.closest(".dynamic-list-row");
        rowContainer.remove();
    }

    getData({toastError = false} = {}) {
        let data = {};

        for (const row of this.listContainer.getElementsByClassName("dynamic-list-row")) {
            const key = row.getElementsByClassName("dynamic-list-key")[0].value;
            const value = row.getElementsByClassName("dynamic-list-value")[0].value;

            if (key == null || key.length == 0) {
                if (toastError) {
                    generateToast(toastError, `"${key}" is not a valid value in the dynamic list and will be skipped.`, "warning");
                }

                console.log(`Invalid dynamic list key value: ${key}`);
                continue;
            }

            data[key] = value;
        }

        return data;
    }
}

customElements.define("dynamic-list", DynamicList);

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

class TableViewer extends HTMLElement {
    constructor() {
        super();

        this.offset = 0;
        this.limit = 10;
        this.container = null;
        this.previousButton = null;
        this.nextButton = null;
    }

    connectedCallback() {
        this.buildContainer();
        this.buildFooter();
        this.reload();
    }

    buildContainer() {
        this.container = document.createElement("div");
        this.showLoading();
        this.append(this.container);
    }

    buildFooter() {
        const footer = document.createElement("div");
        footer.classList.add("row", "mt-3");

        const countContainer = document.createElement("div");
        countContainer.classList.add("col-sm-12", "col-md-6", "align-middle", "ps-3");
        countContainer.innerHTML =
            'Page <span id="page-count">0</span> | <span id="viewer-count">None</span> element(s) located';
        footer.appendChild(countContainer);

        const buttonContainer = document.createElement("div");
        buttonContainer.classList.add("col-sm-12", "col-md-6", "d-flex", "justify-content-end");
        footer.appendChild(buttonContainer);

        this.previousButton = document.createElement("button");
        this.previousButton.classList.add("btn", "btn-sm", "btn-outline-secondary", "me-2");
        this.previousButton.setAttribute("disabled", "");
        this.previousButton.textContent = "Previous Page";
        this.previousButton.addEventListener("click", (event) => {
            this.offset = Math.max(0, this.offset - this.limit);
            this.reload();
        });
        buttonContainer.appendChild(this.previousButton);

        this.nextButton = document.createElement("button");
        this.nextButton.classList.add("btn", "btn-sm", "btn-outline-secondary");
        this.nextButton.setAttribute("disabled", "");
        this.nextButton.textContent = "Next Page";
        this.nextButton.addEventListener("click", (event) => {
            this.offset = this.offset + this.limit;
            this.reload();
        });
        buttonContainer.appendChild(this.nextButton);

        this.append(footer);
    }

    reload() {
        // this.showLoading();

        const apiEndpoint = new URL(window.location.origin + "/" + this.getAttribute("data-endpoint"));
        const error = this.getAttribute("data-error");
        const dataKey = this.getAttribute("data-key");

        apiEndpoint.searchParams.append("offset", this.offset);
        apiEndpoint.searchParams.append("limit", this.limit);

        try {
            tfetch("GET", apiEndpoint.pathname.toString().substring(1) + apiEndpoint.search.toString(), {
                errorTitle: error,
                errorHandler: (jsonError) => {
                    const callback = this.getErrorCallback();
                    callback(jsonError, this.container);
                },
            })
                .then((response) => {
                    if (dataKey == null || !(dataKey in response) || response[dataKey].length == 0) {
                        this.showError(`No data found in response for key ${dataKey}`, "No data found");
                        return;
                    }

                    this.updateCount(response.count);
                    this.updateButtons(response.count);

                    const callback = this.getRenderCallback();
                    this.container.innerHTML = "";

                    for (const rowData of response[dataKey]) {
                        callback(rowData, this.container);
                    }
                })
                .catch((error) => {
                    this.showError(error, "Failed to load");
                });
        } catch (error) {
            this.showError(error, "Failed to load");
        }
    }

    getErrorCallback() {
        const callbackName = this.getAttribute("data-error-callback");

        if (callbackName && window[callbackName]) {
            return window[callbackName];
        }

        throw new Error("Invalid error callback name");
    }

    getRenderCallback() {
        const callbackName = this.getAttribute("data-render-callback");

        if (callbackName && window[callbackName]) {
            return window[callbackName];
        }

        throw new Error("Invalid render callback name");
    }

    showError(consoleError, error) {
        if (consoleError === undefined) {
            return;
        }

        console.error(consoleError || error);
        this.innerHTML = `${error}...`;
    }

    showLoading() {
        // this.container.innerHTML = "Loading...";
        // TODO: reimplement this
    }

    updateCount(text) {
        const viewerCount = document.getElementById("viewer-count");
        viewerCount.textContent = text;

        const pageCount = document.getElementById("page-count");
        pageCount.textContent = Math.floor(this.offset / this.limit);
    }

    updateButtons(count) {
        if (this.offset == count && count == 0) {
            this.previousButton.setAttribute("disabled", "");
            this.nextButton.setAttribute("disabled", "");
            return;
        }

        let previous = this.offset > 0;
        let next = this.offset + this.limit < count;

        if (!previous) {
            this.previousButton.setAttribute("disabled", "");
        } else {
            this.previousButton.removeAttribute("disabled");
        }

        if (!next) {
            this.nextButton.setAttribute("disabled", "");
        } else {
            this.nextButton.removeAttribute("disabled");
        }
    }
}

customElements.define("table-viewer", TableViewer);

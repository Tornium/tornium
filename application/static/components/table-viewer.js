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

class TableViewer extends HTMLElement {
    constructor() {
        super();
    }

    connectedCallback() {
        const shadow = this.attachShadow({mode: "open"});
        this.reload();
    }

    reload() {
        this.showLoading();

        const apiEndpoint = this.getAttribute("data-endpoint");
        const error = this.getAttribute("data-error");
        const dataKey = this.getAttribute("data-key");

        try {
            // TODO: Add error handler after feature/notification is merged
            tfetch("GET", apiEndpoint, {errorTitle: error}).then((response) => {
                if (!(dataKey in response) || response[dataKey].length == 0) {
                    this.showError(`No data found in response for key ${dataKey}`, "No data available");
                    return;
                }

                for (const rowData of response[dataKey]) {
                    // TODO: Insert shadow DOM from render callback into DOM of WebComponent
                    let x = this.getRenderCallback()(rowData);
                    console.log(x);
                }
            });
        } catch (error) {
            this.showError(error, "Failed to load");
        }
    }

    getRenderCallback() {
        const callbackName = this.getAttribute("data-render-callback");
        
        if (callbackName && window[callbackName]) {
            return window[callbackName];
        }

        throw new Error("Invalid render callback name");
    }

    showError(consoleError, error) {
        console.error(consoleError || error);
        this.shadowRoot.innerHTML = `${error}...`;
    }

    showLoading() {
        this.shadowRoot.innerHTML = "Loading...";
    }
}

customElements.define("table-viewer", TableViewer);

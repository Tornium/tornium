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

class AlertConfirm extends HTMLElement {
    constructor() {
        super();

        this.modal = null;
        this.modalContent = null;
        this.modaltitle = null;
        this.headerCloseButton = null;
        this.footerCloseButton = null;
        this.footerAcceptButton = null;

        this.bsModal = null;
    }

    connectedCallback() {
        this.buildModal();
        this.buildHeader();
        this.buildBody();
        this.buildFooter();

        this.bsModal = new bootstrap.Modal(this.modal);
        this.bsModal.show();

        this.headerCloseButton.addEventListener("click", (event) => {
            this.getCallback("data-close-callback")(event);
            this.remove();
        });
        this.footerCloseButton.addEventListener("click", (event) => {
            this.getCallback("data-close-callback")(event);
            this.remove();
        });
        this.footerAcceptButton.addEventListener("click", (event) => {
            this.getCallback("data-accept-callback")(event);
            this.remove();
        });
    }

    buildModal() {
        this.modal = document.createElement("div");
        this.modal.classList.add("modal");
        this.modal.setAttribute("tabindex", -1);
        this.modal.setAttribute("data-bs-backdrop", "static");
        this.append(this.modal);

        const modalDialog = document.createElement("div");
        modalDialog.classList.add("modal-dialog", "modal-dialog-centered");
        this.modal.append(modalDialog);

        this.modalContent = document.createElement("div");
        this.modalContent.classList.add("modal-content");
        modalDialog.append(this.modalContent);
    }

    buildHeader() {
        const modalHeader = document.createElement("div");
        modalHeader.classList.add("modal-header");
        this.modalContent.append(modalHeader);

        this.modalTitle = document.createElement("h1");
        this.modalTitle.classList.add("modal-title", "fs-5");
        this.modalTitle.textContent = this.getAttribute("data-title");
        modalHeader.append(this.modalTitle);

        this.headerCloseButton = document.createElement("button");
        this.headerCloseButton.setAttribute("type", "button");
        this.headerCloseButton.setAttribute("data-bs-dismiss", "modal");
        this.headerCloseButton.classList.add("btn-close");
        modalHeader.append(this.headerCloseButton);
    }

    buildBody() {
        const modalBody = document.createElement("div");
        this.modalContent.append(modalBody);

        const modalBodyP = document.createElement("p");
        modalBodyP.classList.add("pt-2", "px-3");
        modalBodyP.textContent = this.getAttribute("data-body-text");
        modalBody.append(modalBodyP);
    }

    buildFooter() {
        const modalFooter = document.createElement("div");
        modalFooter.classList.add("modal-footer", "border-top-0", "pt-0");
        this.modalContent.append(modalFooter);

        this.footerCloseButton = document.createElement("button");
        this.footerCloseButton.setAttribute("type", "button");
        this.footerCloseButton.setAttribute("data-bs-dismiss", "modal");
        this.footerCloseButton.classList.add("btn", "btn-outline-secondary");
        this.footerCloseButton.textContent = this.getAttribute("data-close-button-text");
        modalFooter.append(this.footerCloseButton);

        this.footerAcceptButton = document.createElement("button");
        this.footerAcceptButton.setAttribute("type", "button");
        this.footerAcceptButton.setAttribute("data-bs-dismiss", "modal");
        this.footerAcceptButton.classList.add("btn", "btn-outline-danger");
        this.footerAcceptButton.textContent = this.getAttribute("data-accept-button-text");
        modalFooter.append(this.footerAcceptButton);
    }

    getCallback(callbackID) {
        const callbackName = this.getAttribute(callbackID);

        if (callbackName == "null") {
            return null;
        } else if (callbackName && window[callbackName]) {
            return window[callbackName];
        }

        throw new Error(`Invalid callback ID ${callbackID}`);
    }
}

customElements.define("alert-confirm", AlertConfirm);

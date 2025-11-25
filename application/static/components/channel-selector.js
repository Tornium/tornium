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

class ChannelSelector extends HTMLSelectElement {
    constructor() {
        super();

        this.initialized = false;
        this.container = null;
        this.testButton = null;
    }

    connectedCallback() {
        if (this.initialized) {
            return;
        }

        this.initialized = true;

        this.container = document.createElement("div");
        this.container.classList.add("d-flex");
        this.before(this.container);
        this.container.append(this);

        this.buildTestButton();
        this.testButton.addEventListener("click", this.testDiscordChannel);
    }

    buildTestButton() {
        this.testButton = document.createElement("button");
        this.testButton.setAttribute("type", "button");
        this.testButton.classList.add("test-discord-channel", "btn", "btn-sm", "btn-outline-secondary");
        this.testButton.innerHTML = `<i class="fa-solid fa-check"></i>`;
        this.after(this.testButton);
    }

    testDiscordChannel = (event) => {
        if (this.value == 0 || this.value == null) {
            return;
        }

        this.testButton.setAttribute("disabled", "");

        tfetch("POST", `bot/server/${guildid}/channels/${this.value}`, {
            errorHandler: (jsonError) => {
                if (jsonError.code === 0 && jsonError.details.code != null && jsonError.details.message != null) {
                    generateToast(
                        "Failed to Send Message",
                        `When trying to send the Discord message to the specified channel, there was the Discord error ${jsonError.details.code}: ${jsonError.details.message}`,
                    );
                } else if (jsonError.code === 4102 && jsonError.details.code) {
                    generateToast(
                        "Failed to Send Message",
                        `When trying to send the Discord message to the specified channel, there was a Discord networking error: HTTP ${jsonError.details.code}`,
                    );
                } else if (jsonError.code === 1) {
                    generateToast(
                        "Successfully Sent Message",
                        "The message was successfully sent to the specified channel.",
                    );
                } else {
                    generateTFetchErrorToast(jsonError, "Failed to Send Message");
                }
            },
        })
            .then((data) => {})
            .finally(() => {
                this.testButton.removeAttribute("disabled");
            });
    };
}

customElements.define("channel-selector", ChannelSelector, { extends: "select" });

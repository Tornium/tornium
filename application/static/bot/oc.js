/* Copyright (C) 2021-2025 tiksan

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

const factionCrimeRanges = {};

function setToolChannel(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/tool/channel`, {
        body: { channel: this.options[this.selectedIndex].value },
        errorTitle: "OC Tool Channel Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Channel Set Successful",
            "The channel for OC missing tool notifications has been successfully set.",
        );
    });
}

function setToolRoles(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedRoles = [];

    selectedOptions.forEach((element) => {
        selectedRoles.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/tool/roles`, {
        body: { roles: selectedRoles },
        errorTitle: "OC Tool Roles Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Roles Set Successful",
            "The roles for OC missing tool notifications have been successfully set.",
        );
    });
}

function setToolCrimes(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedCrimes = [];

    selectedOptions.forEach((element) => {
        selectedCrimes.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/tool/crimes`, {
        body: { crimes: selectedCrimes },
        errorTitle: "OC Tool Crimes Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Crimes Set Successful",
            "The crimes for OC missing tool notifications have been successfully set.",
        );
    });
}

function addRangeCrime(crimeName, container) {
    // TODO: Add range via API

    const crimeListElement = document.createElement("div");
    crimeListElement.classList = ["list-group-item"];
    crimeListElement.setAttribute("data-crime-name", crimeName);

    const label = document.createElement("div");
    label.classList = ["fw-bold"];
    label.textContent = crimeName;
    crimeListElement.append(label);

    const inputGroup = document.createElement("div");
    inputGroup.classList = ["input-group"];

    const minLabel = document.createElement("span");
    const minSelector = document.createElement("input");
    minLabel.textContent = "Min";
    minLabel.classList = ["input-group-text"];
    minSelector.type = "number";
    minSelector.classList = ["form-control"];
    minSelector.setAttribute("aria-label", `Minimum CPR for ${crimeName}`);
    minSelector.value = 0;
    inputGroup.append(minLabel);
    inputGroup.append(minSelector);

    const maxLabel = document.createElement("span");
    const maxSelector = document.createElement("input");
    maxLabel.textContent = "Max";
    maxLabel.classList = ["input-group-text"];
    maxSelector.type = "number";
    maxSelector.classList = ["form-control"];
    maxSelector.setAttribute("aria-label", `Maximum CPR for ${crimeName}`);
    maxSelector.value = 100;
    inputGroup.append(maxLabel);
    inputGroup.append(maxSelector);

    crimeListElement.append(inputGroup);
    container.append(crimeListElement);
}

function removeRangeCrime(crimeName, container) {
    // TOOD: remove range via API
    const element = container.querySelector(`[data-crime-name="${crimeName}"]`);

    if (element == null) {
        console.error("Failed to find crime element");
        return;
    }

    element.remove();
}

function modifyRangeCrimes(event) {
    const factionID = this.getAttribute("data-faction");
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedCrimes = [];

    let listContainer = document.querySelector(`.list-group-range-crimes[data-faction="${factionID}"]`);
    if (listContainer == null) {
        console.error("Failed to find list container");
        return;
    }

    selectedOptions.forEach((element) => {
        selectedCrimes.push(element.getAttribute("value"));
    });

    if (!(factionID in factionCrimeRanges)) {
        factionCrimeRanges[factionID] = [];
    }

    let newCrimes = selectedCrimes.filter((crime) => !factionCrimeRanges[factionID].includes(crime));
    let removedCrimes = factionCrimeRanges[factionID].filter((crime) => !selectedCrimes.includes(crime));
    factionCrimeRanges[factionID] = selectedCrimes;

    newCrimes.forEach((crimeName) => {
        addRangeCrime(crimeName, listContainer);
    });
    removedCrimes.forEach((crimeName) => {
        removeRangeCrime(crimeName, listContainer);
    });

    const defaultMessage = listContainer.querySelector(".default-oc-range-value");
    if (defaultMessage == null) {
        console.error("Failed to find default message");
        return;
    } else if (selectedCrimes.length != 0) {
        defaultMessage.setAttribute("hidden", "");
    } else {
        defaultMessage.removeAttribute("hidden");
    }
}

ready(() => {
    const channelsPromise = channelsRequest();
    const rolesPromise = rolesRequest();

    channelsPromise
        .then(() => {
            document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                let channelID = element.getAttribute("data-selected-channel");
                channelID = channelID == "none" ? "0" : channelID;
                const options = element.querySelectorAll(`option[value="${channelID}"]`);

                if (options.length !== 1) {
                    return;
                }

                options[0].setAttribute("selected", "");
            });
        })
        .finally(() => {
            document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    rolesPromise
        .then(() => {
            document.querySelectorAll(".discord-role-selector").forEach((element) => {
                let roles = parseIntArray(element.getAttribute("data-selected-roles"));

                roles.forEach((roleID) => {
                    const options = element.querySelectorAll(`option[value="${roleID}"]`);

                    if (options.length !== 1) {
                        return;
                    }

                    options[0].setAttribute("selected", "");
                });
            });
        })
        .finally(() => {
            document.querySelectorAll(".discord-role-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    ocNamesRequest()
        .then(() => {
            document.querySelectorAll(".oc-name-selector").forEach((element) => {
                const crimes = parseStringArray(element.getAttribute("data-selected-crimes"));

                crimes.forEach((crimeName) => {
                    const options = element.querySelectorAll(`option[value="${crimeName}"]`);

                    if (options.length !== 1) {
                        return;
                    }

                    options[0].setAttribute("selected", "");
                });
            });
        })
        .then(() => {
            document.querySelectorAll(".oc-range-crimes").forEach((element) => {
                const crimes = parseStringArray(element.getAttribute("data-selected-crimes"));
                const factionid = element.getAttribute("data-faction");
                // TODO: Update `factionCrimeRanges` with values passed

                crimes.forEach((crimeName) => {
                    if (element.querySelectorAll(`option[value="${crimeName}"]`).length !== 1) {
                        return;
                    }

                    addRangeCrime(crimeName);
                });
            });
        })
        .finally(() => {
            document.querySelectorAll(".oc-name-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    document.querySelectorAll(".oc-tool-channel").forEach((element) => {
        element.addEventListener("change", setToolChannel);
    });
    document.querySelectorAll(".oc-tool-roles").forEach((element) => {
        element.addEventListener("change", setToolRoles);
    });
    document.querySelectorAll(".oc-tool-crimes").forEach((element) => {
        element.addEventListener("change", setToolCrimes);
    });
    document.querySelectorAll(".oc-range-crimes").forEach((element) => {
        element.addEventListener("change", modifyRangeCrimes);
    });
});

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

function setDelayedChannel(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/delayed/channel`, {
        body: { channel: this.options[this.selectedIndex].value },
        errorTitle: "OC Tool Channel Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Channel Set Successful",
            "The channel for OC missing delayed notifications has been successfully set.",
        );
    });
}

function setDelayedRoles(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedRoles = [];

    selectedOptions.forEach((element) => {
        selectedRoles.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/delayed/roles`, {
        body: { roles: selectedRoles },
        errorTitle: "OC Tool Roles Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Roles Set Successful",
            "The roles for OC missing delayed notifications have been successfully set.",
        );
    });
}

function setDelayedCrimes(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedCrimes = [];

    selectedOptions.forEach((element) => {
        selectedCrimes.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/delayed/crimes`, {
        body: { crimes: selectedCrimes },
        errorTitle: "OC Tool Crimes Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Crimes Set Successful",
            "The crimes for OC missing delayed notifications have been successfully set.",
        );
    });
}

function setRangeChannel(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/range/channel`, {
        body: { channel: this.options[this.selectedIndex].value },
        errorTitle: "OC Range Channel Set Failed",
    }).then(() => {
        generateToast(
            "OC Range Channel Set Successful",
            "The channel for OC extra-range notifications has been successfully set.",
        );
    });
}

function setRangeRoles(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedRoles = [];

    selectedOptions.forEach((element) => {
        selectedRoles.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/range/roles`, {
        body: { roles: selectedRoles },
        errorTitle: "OC Range Roles Set Failed",
    }).then(() => {
        generateToast(
            "OC Range Roles Set Successful",
            "The roles for OC extra-range notifications have been successfully set.",
        );
    });
}

function setRangeGlobalMin(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/range/minimum`, {
        body: { minimum: this.value },
        errorTitle: "OC Range Global Min Set Failed",
    }).then(() => {
        generateToast(
            "OC Range Global Min Set Successful",
            "The global minimum for OC extra-range notifications have been successfully set.",
        );
    });
}

function setRangeGlobalMax(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/range/maximum`, {
        body: { maximum: this.value },
        errorTitle: "OC Range Global Max Set Failed",
    }).then(() => {
        generateToast(
            "OC Range Global Max Set Successful",
            "The global maximum for OC extra-range notifications have been successfully set.",
        );
    });
}

function insertDOMRangeCrime(crimeName, container) {
    const crimeListElement = document.createElement("div");
    crimeListElement.classList.add("list-group-item");
    crimeListElement.setAttribute("data-crime-name", crimeName);

    const label = document.createElement("div");
    label.classList.add("fw-bold");
    label.textContent = crimeName;
    crimeListElement.append(label);

    const inputGroup = document.createElement("div");
    inputGroup.classList.add("input-group");

    const minLabel = document.createElement("span");
    const minSelector = document.createElement("input");
    minLabel.textContent = "Min";
    minLabel.classList.add("input-group-text");
    minSelector.type = "number";
    minSelector.classList.add("form-control", "oc-range-local-min");
    minSelector.setAttribute("aria-label", `Minimum CPR for ${crimeName}`);
    minSelector.setAttribute("data-crime-name", crimeName);
    minSelector.setAttribute("autocomplete", "off");
    inputGroup.append(minLabel);
    inputGroup.append(minSelector);

    const maxLabel = document.createElement("span");
    const maxSelector = document.createElement("input");
    maxLabel.textContent = "Max";
    maxLabel.classList.add("input-group-text");
    maxSelector.type = "number";
    maxSelector.classList.add("form-control", "oc-range-local-max");
    maxSelector.setAttribute("aria-label", `Maximum CPR for ${crimeName}`);
    maxSelector.setAttribute("data-crime-name", crimeName);
    maxSelector.setAttribute("autocomplete", "off");
    inputGroup.append(maxLabel);
    inputGroup.append(maxSelector);

    crimeListElement.append(inputGroup);
    container.append(crimeListElement);

    minSelector.addEventListener("change", (event) => {
        modifyRangeLocalMinMax(event, "minimum");
    });
    maxSelector.addEventListener("change", (event) => {
        modifyRangeLocalMinMax(event, "maximum");
    });
}

function removeDOMRangeCrime(crimeName, container) {
    const element = container.querySelector(`[data-crime-name="${crimeName}"]`);

    if (element == null) {
        console.error("Failed to find crime element");
        return;
    }

    element.remove();
}

function addRangeCrime(crimeName, container) {
    tfetch("POST", `bot/${guildid}/crimes/${container.getAttribute("data-faction")}/range/local/${crimeName}`, {
        errorTitle: "OC-Specific Range Creation Failed",
    }).then((data) => {
        generateToast(
            "OC-Specific Range Creation Successful",
            "The per-OC configuration for OC extra-range notifications has been successfully created.",
        );

        insertDOMRangeCrime(crimeName, container);

        const minInput = container.querySelector(`.oc-range-local-min[data-crime-name="${crimeName}"]`);
        const maxInput = container.querySelector(`.oc-range-local-max[data-crime-name="${crimeName}"]`);

        if (minInput == null || maxInput == null) {
            console.error("Min input or max input could not be found in the DOM");
            return;
        }

        minInput.value = data.minimum;
        maxInput.value = data.maximum;
    });
}

function removeRangeCrime(crimeName, container) {
    tfetch("DELETE", `bot/${guildid}/crimes/${container.getAttribute("data-faction")}/range/local/${crimeName}`, {
        errorTitle: "OC-Specific Range Deletion Failed",
    })
        .then(() => {
            generateToast(
                "OC-Specific Range Deletion Successful",
                "The per-OC configuration for OC extra-range notifications has been successfully deleted.",
            );
        })
        .then(() => {
            removeDOMRangeCrime(crimeName, container);
        });
}

function modifyRangeCrimes(event) {
    const factionID = this.getAttribute("data-faction");
    const selectedOptions = this.querySelectorAll(":checked");

    let listContainer = document.querySelector(`.list-group-range-crimes[data-faction="${factionID}"]`);
    if (listContainer == null) {
        console.error("Failed to find list container");
        return;
    }

    let selectedCrimes = [];
    selectedOptions.forEach((element) => {
        selectedCrimes.push(element.getAttribute("value"));
    });

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

function modifyRangeLocalMinMax(event, rangeType) {
    const body = {};
    body[rangeType] = event.currentTarget.value;
    console.log(event.currentTarget);
    console.log(event.currentTarget.value);

    const factionID = event.currentTarget.parentElement.parentElement.parentElement.getAttribute("data-faction");
    const crimeName = event.currentTarget.getAttribute("data-crime-name");

    tfetch("PATCH", `bot/${guildid}/crimes/${factionID}/range/local/${crimeName}`, {
        body: body,
        errorTitle: "OC-Specific Range Min/Max Change Failed",
    }).then(() => {
        generateToast(
            "OC-Specific Range Deletion Successful",
            "The per-OC configuration for OC extra-range notifications has been successfully updated.",
        );
    });
}

ready(() => {
    channelsRequest()
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

    rolesRequest()
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
                const factionID = element.getAttribute("data-faction");
                const listContainer = document.querySelector(`.list-group-range-crimes[data-faction="${factionID}"]`);
                factionCrimeRanges[factionID] = crimes;

                if (listContainer == null) {
                    console.error(`Could not find list container for faction ID ${factionID}`);
                    return;
                }

                crimes.forEach((crimeName) => {
                    // TODO: Add event listeners to inputs created by template
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
    document.querySelectorAll(".oc-delayed-channel").forEach((element) => {
        element.addEventListener("change", setDelayedChannel);
    });
    document.querySelectorAll(".oc-delayed-roles").forEach((element) => {
        element.addEventListener("change", setDelayedRoles);
    });
    document.querySelectorAll(".oc-delayed-crimes").forEach((element) => {
        element.addEventListener("change", setDelayedCrimes);
    });
    document.querySelectorAll(".oc-range-channel").forEach((element) => {
        element.addEventListener("change", setRangeChannel);
    });
    document.querySelectorAll(".oc-range-roles").forEach((element) => {
        element.addEventListener("change", setRangeRoles);
    });
    document.querySelectorAll(".oc-range-global-min").forEach((element) => {
        element.addEventListener("change", setRangeGlobalMin);
    });
    document.querySelectorAll(".oc-range-global-max").forEach((element) => {
        element.addEventListener("change", setRangeGlobalMax);
    });
    document.querySelectorAll(".oc-range-crimes").forEach((element) => {
        element.addEventListener("change", modifyRangeCrimes);
    });
});

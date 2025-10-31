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

function setRangeGlobalMin(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/extra-range/minimum`, {
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
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/extra-range/maximum`, {
        body: { maximum: this.value },
        errorTitle: "OC Range Global Max Set Failed",
    }).then(() => {
        generateToast(
            "OC Range Global Max Set Successful",
            "The global maximum for OC extra-range notifications have been successfully set.",
        );
    });
}

function setFeatureChannel(event) {
    tfetch(
        "POST",
        `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/${this.getAttribute("data-feature")}/channel`,
        {
            body: { channel: this.options[this.selectedIndex].value },
            errorTitle: "OC Feature Channel Set Failed",
        },
    ).then(() => {
        generateToast(
            "OC Feature Channel Set Successful",
            "The channel for the feature's notifications has been successfully set.",
        );
    });
}

function setFeatureRoles(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedRoles = [];

    selectedOptions.forEach((element) => {
        selectedRoles.push(element.getAttribute("value"));
    });

    tfetch(
        "POST",
        `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/${this.getAttribute("data-feature")}/roles`,
        {
            body: { roles: selectedRoles },
            errorTitle: "OC Feature Roles Set Failed",
        },
    ).then(() => {
        generateToast(
            "OC Feature Roles Set Successful",
            "The roles for the feature's notifications have been successfully set.",
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

    minSelector.addEventListener("input", (event) => {
        modifyRangeLocalMinMax(event, "minimum");
    });
    maxSelector.addEventListener("input", (event) => {
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
    tfetch("POST", `bot/${guildid}/crimes/${container.getAttribute("data-faction")}/extra-range/local/${crimeName}`, {
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
    tfetch("DELETE", `bot/${guildid}/crimes/${container.getAttribute("data-faction")}/extra-range/local/${crimeName}`, {
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

    tfetch("PATCH", `bot/${guildid}/crimes/${factionID}/extra-range/local/${crimeName}`, {
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
                    maxOptions: null,
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
                    maxOptions: null,
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
            });
        })
        .finally(() => {
            document.querySelectorAll(".oc-name-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    document.querySelectorAll(".discord-channel-selector").forEach((element) => {
        element.addEventListener("change", setFeatureChannel);
    });
    document.querySelectorAll(".discord-role-selector").forEach((element) => {
        element.addEventListener("change", setFeatureRoles);
    });
    document.querySelectorAll(".oc-tool-crimes").forEach((element) => {
        element.addEventListener("change", setToolCrimes);
    });
    document.querySelectorAll(".oc-delayed-crimes").forEach((element) => {
        element.addEventListener("change", setDelayedCrimes);
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
    document.querySelectorAll(".oc-range-local-min").forEach((element) => {
        element.addEventListener("input", (event) => {
            modifyRangeLocalMinMax(event, "minimum");
        });
    });
    document.querySelectorAll(".oc-range-local-max").forEach((element) => {
        element.addEventListener("input", (event) => {
            console.log(event);
            modifyRangeLocalMinMax(event, "maximum");
        });
    });
});

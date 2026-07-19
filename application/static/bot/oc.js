/* Copyr'ight (C) 2021-2025 tiksan

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
let slotData = [];

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

function setMissingMembersDuration(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/missing-member/duration`, {
        body: { minimum_duration: this.value },
        errorTitle: "OC Missing Members Minimum Duration Set Failed",
    }).then(() => {
        generateToast(
            "OC Missing Members Minimum Duration Set successful",
            "The minimum duration for OC missing member notifications has been successfully set.",
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

function removeDOMRangeCrime(crimeName, container) {
    const element = container.querySelector(`[data-crime-name="${crimeName}"]`);

    if (element == null) {
        console.error("Failed to find crime element");
        return;
    }

    element.remove();
}

function modifyRangeLocalMinMax(event, rangeType) {
    const factionID = event.currentTarget.closest("[data-faction]").getAttribute("data-faction");
    const crimeName = event.currentTarget.closest(".col-sm-12").querySelector(".oc-name-selector").value;
    const slotGUID = event.currentTarget.closest("[data-slot-id]").getAttribute("data-slot-id");

    const body = {
        oc_name: crimeName,
    };

    if (event.currentTarget.value == "") {
        body[rangeType] = null;
    } else if (parseInt(event.currentTarget.value) != NaN) {
        body[rangeType] = parseInt(event.currentTarget.value);
    } else {
        generateToast("Invalid CPR", "The CPR must be an integer between 0 and 100.");
        return;
    }

    tfetch("PATCH", `bot/${guildid}/crimes/${factionID}/extra-range/local/${slotGUID}`, {
        body: body,
        errorTitle: "OC Slot-Specific Range Min/Max Change Failed",
    }).then(() => {
        generateToast(
            "OC-Specific Range Updated Successfully",
            "The per-OC slot configuration for OC extra-range notifications has been successfully updated.",
        );
    });
}

function reloadRangeCrime(event) {
    const factionID = this.getAttribute("data-faction");
    const ocName = this.value;

    const slotsRangeContainer = this.parentElement.querySelector(".list-group-range-slots");
    slotsRangeContainer.innerHTML = "";

    if (ocName == "") {
        slotsRangeContainer.setAttribute("hidden", "");
        return;
    }

    tfetch("GET", `faction/${factionID}/crime/cpr-range`, { errorTitle: "OC CPR Ranges Fetch Failed" }).then(
        (slotRanges) => {
            const crimeSlots = slotData.filter((slot) => slot.oc == ocName);
            crimeSlots.forEach((slot) => {
                const slotRange =
                    ocName in slotRanges.local
                        ? slotRanges.local[ocName].find(
                              (rangeData) =>
                                  rangeData.position_name == slot.position_name &&
                                  rangeData.position_index == slot.position_index,
                          )
                        : null;
                appendSlotRange(slot, slotRange, slotsRangeContainer);
            });
            slotsRangeContainer.removeAttribute("hidden");
        },
    );
}

function appendSlotRange(slot, slotRange, container) {
    const slotElement = document.createElement("div");
    slotElement.setAttribute("data-slot-id", slot.guid);
    slotElement.classList.add("list-group-item", "justify-content-between", "align-items-center");
    container.append(slotElement);

    const label = document.createElement("span");
    label.textContent = `${slot.position_name} #${slot.position_index}`;
    slotElement.append(label);

    const rangeContainer = document.createElement("div");
    rangeContainer.classList.add("d-flex", "flex-wrap", "flex-md-nowrap", "align-items-center", "gap-2");
    slotElement.append(rangeContainer);

    const minRangeGroup = document.createElement("div");
    minRangeGroup.classList.add("input-group", "input-group-sm");
    rangeContainer.append(minRangeGroup);

    const minRangeLabel = document.createElement("label");
    minRangeLabel.classList.add("input-group-text");
    minRangeLabel.textContent = "Min";
    minRangeGroup.append(minRangeLabel);

    const minRangeInput = document.createElement("input");
    minRangeInput.classList.add("form-control");
    minRangeInput.setAttribute("type", "number");
    minRangeInput.setAttribute("placeholder", "Global default");
    minRangeInput.setAttribute("autocomplete", "off");
    minRangeGroup.append(minRangeInput);
    if (slotRange != null) {
        minRangeInput.value = slotRange.minimum;
    }

    const maxRangeGroup = document.createElement("div");
    maxRangeGroup.classList.add("input-group", "input-group-sm");
    rangeContainer.append(maxRangeGroup);

    const maxRangeLabel = document.createElement("label");
    maxRangeLabel.classList.add("input-group-text");
    maxRangeLabel.textContent = "Max";
    maxRangeGroup.append(maxRangeLabel);

    const maxRangeInput = document.createElement("input");
    maxRangeInput.classList.add("form-control");
    maxRangeInput.setAttribute("type", "number");
    maxRangeInput.setAttribute("placeholder", "Global default");
    maxRangeInput.setAttribute("autocomplete", "off");
    maxRangeGroup.append(maxRangeInput);
    if (slotRange != null) {
        maxRangeInput.value = slotRange.maximum;
    }

    minRangeInput.addEventListener("change", (event) => {
        modifyRangeLocalMinMax(event, "minimum");
    });
    maxRangeInput.addEventListener("change", (event) => {
        modifyRangeLocalMinMax(event, "maximum");
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
                    plugins: ["remove_button"],
                });
            });
        });

    ocNamesRequest()
        .then(() => {
            document.querySelectorAll(".oc-name-selector").forEach((element) => {
                const selectedCrimesString = element.getAttribute("data-selected-crimes");

                if (selectedCrimesString == null) {
                    return;
                }

                const crimes = parseStringArray(selectedCrimesString);

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
                const factionID = element.getAttribute("data-faction");
                const listContainer = document.querySelector(`.list-group-range-crimes[data-faction="${factionID}"]`);

                const emptyOption = document.createElement("option");
                emptyOption.value = "";
                emptyOption.textContent = "Select an OC type...";
                emptyOption.setAttribute("selected", "");
                element.prepend(emptyOption);

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
                    plugins: ["remove_button"],
                });
            });
        });

    tfetch("GET", "faction/crime/slots", {
        errorTitle: "OC Slot Data Load Failed",
    }).then((data) => {
        slotData = data;
    });

    document.querySelectorAll(".oc-missing-member-duration").forEach((element) => {
        const selectedDuration = element.getAttribute("data-selected-duration");
        const options = element.querySelectorAll(`option[value="${selectedDuration}"]`);

        if (options.length === 1) {
            options[0].setAttribute("selected", "");
        }

        new TomSelect(element, {
            create: false,
            maxOptions: null,
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
    document.querySelectorAll(".oc-missing-member-duration").forEach((element) => {
        element.addEventListener("change", setMissingMembersDuration);
    });
    document.querySelectorAll(".oc-range-global-min").forEach((element) => {
        element.addEventListener("change", setRangeGlobalMin);
    });
    document.querySelectorAll(".oc-range-global-max").forEach((element) => {
        element.addEventListener("change", setRangeGlobalMax);
    });
    document.querySelectorAll(".oc-range-crimes").forEach((element) => {
        element.addEventListener("change", reloadRangeCrime);
    });
});

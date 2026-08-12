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

const factionID = document.currentScript.getAttribute("data-faction-id");
let steadfastInputs = {
    strength: null,
    defense: null,
    speed: null,
    dexterity: null,
};
let timestampInputs = {
    from: null,
    to: null,
};
let timestampErrorMessage = null;

function validateSteadfastValue(stat, statSteadfast) {
    if (typeof statSteadfast === "number" && statSteadfast >= 0 && statSteadfast <= 20) {
        steadfastInputs[stat].classList.toggle("is-invalid", false);
        return true;
    }

    steadfastInputs[stat].classList.toggle("is-invalid", true);
    return false;
}

function validateTimestamp(timestampType, timestamp) {
    if (typeof timestamp == "number" && timestamp > 0) {
        timestampInputs[timestampType].classList.toggle("is-invalid", false);
        return true;
    }

    timestampErrorMessage.textContent = `The ${timestampType} timestamp must be a valid timestamp.`;
    timestampInputs[timestampType].classList.toggle("is-invalid", true);
    return false;
}

function createEvent() {
    const statsSteadfast = {
        strength: parseInt(steadfastInputs.strength.value),
        defense: parseInt(steadfastInputs.defense.value),
        speed: parseInt(steadfastInputs.speed.value),
        dexterity: parseInt(steadfastInputs.dexterity.value),
    };
    const timestamps = {
        from: timestampInputs.from.value,
        to: timestampInputs.to.value,
    };

    let allValid = true;
    for (const [stat, statSteadfast] of Object.entries(statsSteadfast)) {
        const statValidity = validateSteadfastValue(stat, statSteadfast);

        if (statValidity == false) {
            allValid = false;
        }
    }

    for (const [timestampType, timestamp] of Object.entries(timestamps)) {
        const timestampValidity = validateTimestamp(timestampType, timestamp);

        if (timestampValidity == false) {
            allValid = false;
        }
    }

    if (timestamps.from > timestamps.to) {
        timestampErrorMessage.textContent = "The from timestamp must be before the to timestamp.";
        timestampInputs.from.classList.toggle("is-invalid", true);
        allValid = false;
    }

    if (!allValid) {
        return;
    }

    tfetch("POST", `faction/${factionID}/calendar/steadfast`, {
        body: {
            steadfast: statsSteadfast,
            from: timestamps.from,
            to: timestamps.to,
        },
        errorTitle: "Steadfast Event Creation Failed",
    }).then((response) => {
        window.location.href = "/faction/calendar";
    });
}

ready(() => {
    steadfastInputs.strength = document.getElementById("steadfast-strength");
    steadfastInputs.defense = document.getElementById("steadfast-defense");
    steadfastInputs.speed = document.getElementById("steadfast-speed");
    steadfastInputs.dexterity = document.getElementById("steadfast-dexterity");
    timestampInputs.from = document.getElementById("steadfast-from-timestamp");
    timestampInputs.to = document.getElementById("steadfast-to-timestamp");
    timestampErrorMessage = document.getElementById("steadfast-timestamp-error");

    const createButton = document.getElementById("create-event");
    createButton.addEventListener("click", createEvent);
});

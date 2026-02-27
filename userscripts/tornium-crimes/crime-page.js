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

import { waitForElement } from "./dom.js";
import { torniumFetch } from "./api.js";
import { log } from "./logging.js";

export function injectMemberSelector(container, userID, factionID) {
    if (container == null) {
        return;
    }

    const wrapper = document.createElement("div");
    container.after(wrapper);

    const seperator = document.createElement("hr");
    seperator.classList.add("page-head-delimiter", "m-top10", "m-bottom10");
    wrapper.append(seperator);

    torniumFetch(`faction/${factionID}/members`, {}).then((memberData) => {
        const label = document.createElement("label");
        label.setAttribute("for", "tornium-crimes-optimum-member");
        label.textContent = "Faction Member (Optimum OC): ";
        wrapper.append(label);

        const selector = document.createElement("select");
        selector.setAttribute("name", "tornium-crimes-optimum-member");
        wrapper.append(selector);

        for (const member of memberData) {
            const option = document.createElement("option");
            option.setAttribute("value", member.ID);
            option.textContent = member.name;
            selector.append(option);
        }

        selector.value = userID;
        selector.addEventListener("change", onSelectedMemberChange);
    });
}

export function updateMemberOptimums(optimumData) {
    console.log(optimumData);
    // If the user has TT enabled, TT may inject .tt-oc2-list
    // See https://github.com/Mephiles/torntools_extension/blob/501eba808e20354f748563e8692da418267c6c48/extension/scripts/content/factions/ttFactions.ts#L89
    Promise.any([
        waitForElement(".tt-oc2-list"),
        waitForElement(`#faction-crimes-root hr.page-head-delimiter + div:has(> div[class^="wrapper___"][data-oc-id])`),
    ]).then((root) => {
        if (!root.classList.contains("tt-oc2-list")) {
            root.classList.add("tt-oc2-list");
        }

        // TODO: Add a mutation observer upon the root if one does not exist and tie it into a function to update the data

        const crimeElements = root.querySelectorAll(`[class*="wrapper___"][data-oc-id]`);

        for (const crimeElement of crimeElements) {
            const crimeID = parseInt(crimeElement.getAttribute("data-oc-id"));
            const slotElements = crimeElement.querySelectorAll(
                `[class*="wrapper___"]:has(> button[class*="slotHeader___"])`,
            );

            if (crimeID == null || slotElements.length === 0) {
                continue;
            }

            for (const slotElement of slotElements) {
                const titleElement = slotElement.querySelector(`span[class*="title___"]`);
                const badgeContainer = slotElement.querySelector(`[class*="badgeContainer___"]`);
                badgeContainer.classList.add("tornium-crimes-slot-badge-container");

                if (badgeContainer == null || titleElement == null) {
                    continue;
                }

                const slotData = optimumData.find((optimumSlotData) => {
                    return (
                        optimumSlotData.oc_id == crimeID &&
                        `${optimumSlotData.oc_position} #${optimumSlotData.oc_position_index}` ==
                            titleElement.textContent
                    );
                });

                if (slotData == null) {
                    continue;
                }

                const slotInfo = document.createElement("div");
                slotInfo.classList.add("tornium-crimes-slot-info");
                slotInfo.textContent = `ΔEV: ${(slotData.team_expected_value_change * 100).toFixed(2)}%; ΔEV': ${(slotData.user_expected_value_change * 100).toFixed(2)}%; ΔP: ${(slotData.team_probability_change * 100).toFixed(2)}%`;
                badgeContainer.prepend(slotInfo);
            }
        }
    });
}

function onSelectedMemberChange(event) {
    torniumFetch("user", { ttl: 1000 * 60 * 60 })
        .then((identityData) => {
            return identityData.factiontid;
        })
        .then((factionID) => {
            return torniumFetch(`faction/${factionID}/crime/member/${event.target.value}/optimum`, { ttl: 60 });
        })
        .then((optimumData) => {
            return updateMemberOptimums(optimumData);
        });
}

export function injectStyles() {
    GM_addStyle(".tornium-crimes-slot-info {padding-top: 0.5em; padding-bottom: 0.5em; margin: 0.25em;}");
    GM_addStyle(".tornium-crimes-slot-badge-container {flex-wrap: wrap; padding-bottom: 0.25em;}");
    GM_addStyle(`div[class*="slotBody___"] {height: inherit; height: stretch; height: -webkit-fill-available; height: 100%; min-height: 32px;}`);
}

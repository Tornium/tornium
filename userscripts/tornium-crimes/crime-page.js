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

export function updateMemberOptimums(optimumData) {}

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

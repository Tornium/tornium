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

export function createProfileContainer() {
    const parentContainer = document.querySelector("div.content-title");

    const container = document.createElement("div");
    container.classList.add("tornium-estimate-profile-container");
    parentContainer.append(container);

    const statsElement = document.createElement("p");
    statsElement.innerText = "Stats: ";
    container.append(statsElement);

    const statsSpan = document.createElement("span");
    statsSpan.setAttribute("id", "tornium-estimate-profile-stats");
    statsSpan.innerText = "Loading...";
    statsElement.append(statsSpan);

    const estimateElement = document.createElement("p");
    estimateElement.innerText = "Estimate: ";
    container.append(estimateElement);

    const estimateSpan = document.createElement("span");
    estimateSpan.setAttribute("id", "tornium-estimate-profile-estimate");
    estimateSpan.innerText = "Loading...";
    estimateElement.append(estimateSpan);

    return [statsSpan, estimateSpan];
}

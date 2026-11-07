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

function loadCrimeGraph() {
    const viewer = document.getElementById("oc-graph-viewer");
    const ocName = this.value;

    if (viewer == null || ocName == "") {
        return;
    }

    viewer.innerHTML = "";

    const crimeGraphImage = document.createElement("img");
    crimeGraphImage.src = `/torn/crimes/graphs/${ocName}.svg`;
    viewer.append(crimeGraphImage);
}

ready(() => {
    const ocNamesPromise = ocNamesRequest();

    ocNamesPromise.then(() => {
        document.querySelectorAll(".oc-name-selector").forEach((element) => {
            const emptyOption = document.createElement("option");
            emptyOption.value = "";
            emptyOption.textContent = "Select an OC type...";
            emptyOption.setAttribute("selected", "");
            element.prepend(emptyOption);

            new TomSelect(element, { create: false });
        });

        document.querySelectorAll(".oc-name-selector").forEach((element) => {
            element.addEventListener("change", loadCrimeGraph);
        });
    });
});

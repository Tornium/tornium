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
let factionMembers = null;

$.fn.dataTable.ext.pager.numbers_length = 5;

function loadViewerCPR(ocName, cprData) {
    if (factionMembers == null) {
        generateToast(
            "Members Not Loaded",
            "The members of your faction are not yet loaded. Wait for them to load first.",
        );
        return;
    }

    const viewer = document.getElementById("viewer");
    viewer.setAttribute("data-oc-name", ocName);
    viewer.innerHTML = "";

    const viewerTable = document.createElement("table");
    viewerTable.classList.add("table", "table-striped", "w-100");
    viewer.append(viewerTable);

    const viewerTableHead = document.createElement("thead");
    const viewerTableHeadRow = document.createElement("tr");
    viewerTableHead.append(viewerTableHeadRow);
    viewerTable.append(viewerTableHead);

    const ocPositions = Object.keys(cprData);
    const membersData = [];

    Object.keys(factionMembers).forEach((memberID) => {
        const memberData = [`${factionMembers[memberID].name} [${memberID}]`];

        ocPositions.forEach((ocPosition) => {
            const memberPositionCPR = cprData[ocPosition].find((member) => member.id == memberID);
            memberData.push(memberPositionCPR ? memberPositionCPR.cpr : null);
        });

        membersData.push(memberData);
    });

    ocPositions.unshift("Faction Member");
    ocPositions.forEach((ocPosition) => {
        const viewerTableColumnName = document.createElement("th");
        viewerTableColumnName.innerText = ocPosition;
        viewerTableHeadRow.append(viewerTableColumnName);
    });

    const viewerDataTable = new DataTable(viewerTable, {
        responsive: false,
        data: membersData,
        ordering: true,
        searching: false,
        order: [[0, "desc"]],
        scrollX: true,
    });
}

function loadViewer(event) {
    const ocName = this.value;
    tfetch("GET", `faction/${factionID}/crime/cpr/${ocName}`, {
        errorTitle: "CPR Retrieval Failed",
    }).then((data) => {
        loadViewerCPR(ocName, data);
    });
}

function clearViewer() {
    const viewer = document.getElementById("viewer");
    viewer.innerHTML = "";

    const defaultViewer = document.createElement("p");
    defaultViewer.classList.add("card-text");
    defaultViewer.setAttribute("id", "viewer-default");
    defaultViewer.textContent = "Select an OC name first.";
    viewer.appendChild(defaultViewer);

    document.getElementById("viewer-title").textContent = "OC Viewer";
}

ready(() => {
    clearViewer();

    const memberPromise = tfetch("GET", `faction/${factionID}/members`, {
        errorTitle: "Faction Members Retrieval Failed",
    }).then((data) => {
        factionMembers = data.reduce((obj, member) => ((obj[member.ID] = member), obj), {});
    });

    const ocNamesPromise = ocNamesRequest().then(() => {
        document.querySelectorAll(".oc-name-selector").forEach((element) => {
            new TomSelect(element, {
                create: false,
            });
        });
    });

    Promise.all([memberPromise, ocNamesPromise]).then(() => {
        document.querySelectorAll(".oc-name-selector").forEach((element) => {
            element.addEventListener("change", loadViewer);
        });
    });
});

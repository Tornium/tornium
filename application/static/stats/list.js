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

const defaultMessage = document.getElementById("default-chain-list-text");
const viewer = document.getElementById("chain-list-viewer");

const minimumDifficultySelector = document.getElementById("config-minimum-difficulty");
const maximumDifficultySelector = document.getElementById("config-maximum-difficulty");
const minimumLevelInput = document.getElementById("config-minimum-level");
const maximumLevelInput = document.getElementById("config-maximum-level");
const sortBySelector = document.getElementById("config-sort-by");
const limitSelector = document.getElementById("config-limit");
const inactiveToggle = document.getElementById("config-inactive-only");
const factionlessToggle = document.getElementById("config-factionless-only");

const viewerTableHeaders = [
    "User",
    "Faction",
    "Last Action",
    "Last User Update",
    "Stat Added",
    "Stat Score",
    "Fair Fight",
    "Respect",
];

function generateChainList() {
    const options = {
        minimum_difficulty: parseFloat(minimumDifficultySelector.value),
        maximum_difficulty: parseFloat(maximumDifficultySelector.value),
        minimum_level: parseInt(minimumLevelInput.value),
        maximum_level: parseInt(maximumLevelInput.value),
        sort_order: sortBySelector.value,
        limit: parseInt(limitSelector.value),
        inactive: inactiveToggle.checked,
        factionless: factionlessToggle.checked,
    };

    tfetch("POST", `stat/chain-list`, { body: options, errorTitle: "Chain List Request Failed" }).then(
        (chainListData) => {
            clearTable();

            if (chainListData.length == 0) {
                showDefaultMessage();
                defaultMessage.innerText = "No targets found...";
                return;
            }

            hideDefaultMessage();
            buildViewer(chainListData);
        },
    );
}

function clearTable() {
    viewer.innerHTML = "";
}

function hideDefaultMessage() {
    defaultMessage.setAttribute("hidden", "");
}

function showDefaultMessage() {
    defaultMessage.removeAttribute("hidden");
}

function buildViewer(chainListData) {
    const viewerTable = document.createElement("table");
    viewerTable.classList.add("table", "table-striped", "card-table", "w-100");
    viewerTable.id = "viewer-table";
    viewer.append(viewerTable);

    const viewerTableHead = document.createElement("thead");
    const viewerTableHeadRow = document.createElement("tr");
    viewerTableHeaders.forEach((columnName) => {
        const viewerTableColumnName = document.createElement("th");
        viewerTableColumnName.innerText = columnName;
        viewerTableHeadRow.append(viewerTableColumnName);
    });
    viewerTableHead.append(viewerTableHeadRow);
    viewerTable.append(viewerTableHead);

    const chainListTargets = [];
    const idNameMap = {};
    Array.from(chainListData).forEach((chainTarget) => {
        idNameMap[chainTarget.target.ID] = chainTarget.target.name;
        chainListTargets.push([
            chainTarget.target.ID,
            chainTarget.target.faction ? chainTarget.target.faction.name : "",
            chainTarget.target.last_action,
            chainTarget.target.last_refresh,
            chainTarget.time_added,
            chainTarget.stat_score,
            chainTarget.fair_fight,
            chainTarget.respect,
        ]);
    });

    const viewerDataTable = new DataTable(viewerTable, {
        responsive: false,
        data: chainListTargets,
        ordering: true,
        searching: false,
        order: [[0, "desc"]],
        scrollX: true,
        columns: [
            {
                // User
                title: "User",
                render: function (data, type, row, meta) {
                    return `<label>User: </label><a href="https://www.torn.com/profiles.php?XID=${data}">${idNameMap[data]} [${data}]</a>`;
                },
            },
            {
                // Faction
                title: "Faction",
                render: function (data, type, row, meta) {
                    return `<label>Faction: </label>${data}`;
                },
            },
            {
                // Last Action
                title: "Last Action",
                render: function (data, type, row, meta) {
                    return `<label>Last Action: </label>${reltime(data)}`;
                },
            },
            {
                // User Refresh
                title: "Last User Update",
                render: function (data, type, row, meta) {
                    return `<label>Last User Update: </label>${reltime(data)}`;
                },
            },
            {
                // Stat insert timestamp
                title: "Stat Added",
                render: function (data, type, row, meta) {
                    return `<label>Stat Added: </label>${reltime(data)}`;
                },
            },
            {
                // Stat Score
                title: "Stat Score",
                render: function (data, type, row, meta) {
                    return `<label>Stat Score: </label>${commas(data)}`;
                },
            },
            {
                // Fair Fight
                title: "Fair Fight",
                render: function (data, type, row, meta) {
                    return `<label>Fair Fight: </label>${data}`;
                },
            },
            {
                // Respect
                title: "Respect",
                render: function (data, type, row, meta) {
                    return `<label>Respect: </label>${data}`;
                },
            },
        ],
    });
}

ready(() => {
    new TomSelect(minimumDifficultySelector, { create: true });
    new TomSelect(maximumDifficultySelector, { create: true });
    new TomSelect(sortBySelector, { create: false });
    new TomSelect(limitSelector, { create: true });

    document.getElementById("generate-list-button").addEventListener("click", generateChainList);
});

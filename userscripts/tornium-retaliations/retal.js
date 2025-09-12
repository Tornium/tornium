import { torniumFetch } from "./api.js";
import { waitForElement } from "./dom.js";

export function fetchRetaliations(factionID) {
    torniumFetch(`faction/${factionID}/attacks/retaliations`).then((retaliations) => {
        return retaliations;
    });
}

export function createRetaliationContainer() {
    waitForElement("#faction_war_list_id").then((parent) => {
        const container = document.createElement("div");
        container.classList.add("tornium-retaliations-container");
        parent.after(container);

        const retalSection = document.createElement("fieldset");
        const retalLegend = document.createElement("legend");
        retalLegend.innerText = "Retaliations";
        retalSection.append(retalLegend);

        const retalTable = document.createElement("table");
        retalTable.classList.add("tornium-retaliations-table");

        const retalTableHead = document.createElement("thead");
        retalTableHead.innerHTML = `
            <tr>
                <th>User</th>
                <th>Timeout</th>
            </tr>
        `;
        retalTable.append(retalTableHead);

        const retalTableBody = document.createElement("tbody");
        retalTable.append(retalTableBody);
        retalSection.append(retalTable);

        container.append(retalSection);
    });

    injectRetaliationStyles();
}

export function renderRetaliationContainer(retaliations) {}

function injectRetaliationStyles() {
    GM_addStyle(`
        .tornium-retaliations-container {
            margin-top: 10px;
        }

        .tornium-retaliations-container hr {
            border: none;
            border-top: 1px solid #444;
            margin-top: 20px !important;
            margin-bottom: 20px !important;
        }

        .tornium-retaliations-container fieldset {
            border: 1px solid #555;
            border-radius: 6px;
            padding: 16px;
            margin-bottom: 20px;
            background: rgba(0, 0, 0, 0.25);
        }

        .tornium-retaliations-container legend {
            font-size: 1.2rem;
            font-weight: bold;
            padding: 0 6px;
            color: #fff;
        }

        .tornium-retaliations-container table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            color: #ddd;
        }

        .tornium-retaliations-container th,
        .tornium-retaliations-container td {
            padding: 6px 10px;
            border-bottom: 1px solid #444;
            text-align: left;
        }

        .tornium-retaliations-container th {
            color: #fff;
        }

        .tornium-retaliations-container a {
            color: #4aa3ff;
            text-decoration: none;
        }

        .tornium-retaliations-container a:hover {
            text-decoration: underline;
        }

        .tornium-retaliations-container .torn-btn {
            display: inline-block;
            margin: 8px 6px 0 0;
        }
    `);
}

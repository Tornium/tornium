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
import { GM_PREFIX } from "./constants.js";
import { log } from "./logging.js";

export async function startScenarioExporterListener() {
    const factionID = GM_getValue(`${GM_PREFIX}:factionID`);
    if (factionID == null) {
        log("Unable to get faction ID of user... aborting.");
        return;
    }

    const originalFetch = (unsafeWindow || window).fetch;
    (unsafeWindow || window).fetch = async function (resource, options) {
        if (!document.hasFocus()) {
            return originalFetch.call(this, resource, options);
        }

        // The resource can be provided as either a string or any object with a stringifier
        // such as a URL or as a Request object. We need to determine if the URL of the request
        // matches that of Torn's request for fetch OC data.
        let url = null;
        let body = null;

        if (typeof resource === "string" || resource instanceof String) {
            url = new URL(resource, window.location.origin);
            body = options.body;
        } else if (resource instanceof Request) {
            url = new URL(resource.url);
            body = resource.body || options.body;
        } else {
            log("Unable to determine type of request... defaulting to window.fetch.");
            return await originalFetch.call(this, resource, options);
        }

        if (!(url instanceof URL) || !(url.searchParams instanceof URLSearchParams)) {
            log("Unable to determine URL of request... defaulting to window.fetch.");
            return await originalFetch.call(this, resource, options);
        } else if (url.hostname != "www.torn.com" || url.pathname != "/page.php") {
            return await originalFetch.call(this, resource, options);
        } else if (
            url.searchParams.get("sid") != "organizedCrimesData" ||
            url.searchParams.get("step") != "crimeList"
        ) {
            return await originalFetch.call(this, resource, options);
        } else if (!(body instanceof FormData)) {
            log("Unable to determine body of request... defaulting to window.fetch.");
            return await originalFetch.call(this, resource, options);
        } else if (body.get("group")?.toLowerCase() != "completed") {
            return await originalFetch.call(this, resource, options);
        }

        const response = await originalFetch.call(this, resource, options);

        const responseExportCopy = response.clone();
        setTimeout(() => {
            // We don't want to block Torn's rendering, so we should seperate this with a
            // setTimeout to allow the return first.
            exportScenarios(responseExportCopy, factionID);
        }, 0);

        return response;
    };
}

async function exportScenarios(scenarioResponse, factionID) {
    const scenarioData = await scenarioResponse.json();

    torniumFetch(`faction/${factionID}/crime/scenarios`, { method: "POST", body: scenarioData }).then((response) => {
        log(`Uploaded OC scenarios resulting in code ${response.code}: ${response.message}`);
    });
}

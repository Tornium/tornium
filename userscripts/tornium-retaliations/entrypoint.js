import { DEBUG } from "./constants.js";
import { log } from "./logging.js";
import { isAuthExpired } from "./oauth.js";
import { createSettingsButton } from "./settings.js";

log(`Loading userscript${DEBUG ? " with debug" : ""}...`);

if (!isAuthExpired()) {
    log("Access token has expired and needs to be set again.");
    // TODO: Handle this
} else {
    // TODO: Use an observer against the faction page if the URL is the faction page
    createSettingsButton();

    // TODO: Load settings and other UI elements
}

import { log } from "./logging.js";

export function createSettingsButton() {
    if (!window.pathname.startsWith("/faction.php")) {
        // The settings link will only be loaded from the faction page
        return;
    }

    const pageTitleElement = window.getElementById("skip-to-content");

    if (pageTitleElement == undefined) {
        log("Missing page title element");
        return;
    }

    const settingsButton = document.createElement("a");
    settingsButton.classList.add("t-clear");
    pageTitleElement.after(settingsButton);
}

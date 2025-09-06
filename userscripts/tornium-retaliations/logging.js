import { DEBUG } from "./constants.js";

export function log(string) {
    if (!DEBUG) {
        return;
    }

    console.log("[Tornium Retaliations] " + window.location.pathname + " - " + string);
}

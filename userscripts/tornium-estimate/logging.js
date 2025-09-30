import { DEBUG } from "./constants.js";

export function log(string) {
    if (!DEBUG) {
        return;
    }

    console.log("[Tornium Estimate] " + window.location.pathname + " - " + string);
}

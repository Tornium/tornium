import { torniumFetch } from "./api.js";

export function fetchRetaliations(factionID) {
    torniumFetch(`faction/${factionID}/attacks/retaliations`).then((retaliations) => {
        return retaliations;
    });
}

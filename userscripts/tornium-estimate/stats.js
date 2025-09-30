import { torniumFetch } from "./api.js";
import { log } from "./logging.js";

export function getSingleStats(userID) {
    const statsPromise = torniumFetch(`user/${userID}/stat`, {});
    const estimatePromise = torniumFetch(`user/estimate/${userID}`, {});
}

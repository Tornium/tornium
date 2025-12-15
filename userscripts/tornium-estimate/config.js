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

import { log } from "./logging.js";

export const PAGE_OPTIONS = [
    { id: "profile", label: "Profile Page" },
    { id: "faction-rw", label: "Faction Ranked War" },
    { id: "search", label: "Advanced Search" },
    { id: "attack-loader", label: "Attack Loader" },
];

export const Config = new Proxy(
    class {
        static defaults = {
            exactStat: false,
            pages: [],
            statScore: null,
        };
    },
    {
        get(target, prop, receiver) {
            // Ignore function accesses
            if (prop in target && typeof target[prop] === "function") return Reflect.get(target, prop, receiver);

            // Ignore non-default or internal props
            if (prop === "defaults" || prop === "name" || prop === "prototype")
                return Reflect.get(target, prop, receiver);

            const defaults = target.defaults || {};
            const def = prop in defaults ? defaults[prop] : undefined;

            return GM_getValue(`tornium-estimate:config:${prop}`, def);
        },

        set(target, prop, value, receiver) {
            log(`Set ${prop} to ${value}`);
            GM_setValue(`tornium-estimate:config:${prop}`, value);

            return true;
        },

        ownKeys(target) {
            return Reflect.ownKeys(target.defaults || {});
        },
    },
);

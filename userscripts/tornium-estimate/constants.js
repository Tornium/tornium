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

export const DEBUG = false;
export const BASE_URL = DEBUG ? "http://127.0.0.1:5000" : "https://tornium.com";
export const ENABLE_LOGGING = true;
export const VERSION = "1.0.0-dev";
export const APP_ID = "6be7696c40837f83e5cab139e02e287408c186939c10b025";
export const APP_SCOPE = "torn_key:usage";

// Tampermonkey will store data from GM_setValue separately in its userscript storage,
// however TPDA, violentmonkey, and others will store data from GM_setValue in localStorage
GM_setValue("tornium-estimate:test", "1");
export const clientLocalGM = localStorage.getItem("tornium-estimate:test") === "1";

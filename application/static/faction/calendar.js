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

const factionID = document.currentScript.getAttribute("data-faction-id");
let calendarViewSelector = null;
let calendarTimelineControls = null;
let calendarTimeline = null;
let calendarGrid = null;

(async () => {
    // We need to polyfill Temporal as it's not yet available on Safari and on iOS
    if (typeof window.Temporal === "undefined") {
        console.log("polyfilling Temporal");
        await import("https://cdn.jsdelivr.net/npm/@js-temporal/polyfill@0.5.1/dist/index.umd.min.js");
        window.Temporal = Temporal;
    }

    const now = Temporal.Now.instant();
    console.log(now);
})();

function toggleCalendarView(event) {
    const selectedView = event.target.value;

    if (calendarTimeline == null || calendarGrid == null) {
        console.error("The calendar timeline and/or grid view(s) could not be found.");
        return;
    }

    if (selectedView == "timeline") {
        calendarTimeline.removeAttribute("hidden");
        calendarTimelineControls.removeAttribute("hidden");
        calendarGrid.setAttribute("hidden", "");
        return;
    } else if (selectedView == "calendar") {
        calendarTimeline.setAttribute("hidden", "");
        calendarTimelineControls.setAttribute("hidden", "");
        calendarGrid.removeAttribute("hidden");
        return;
    }

    console.error(`Invalid calendar view ${selectedView}`);
}

ready(() => {
    calendarViewSelector = document.getElementById("view-type-list");
    calendarTimeline = document.querySelector("calendar-timeline");
    calendarTimelineControls = document.querySelector("calendar-timeline-controls");
    calendarGrid = document.querySelector("calendar-grid");

    calendarViewSelector.addEventListener("change", toggleCalendarView);
});

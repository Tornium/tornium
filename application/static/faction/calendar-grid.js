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

const CALENDAR_GRID_MONTHS_RENDER = 3;

class CalendarGrid extends HTMLElement {
    static observedAttributes = ["hidden"];

    constructor() {
        super();

        // Current page: by default, this is from the start of the current month to ~3 months in the future
        this.fromTimestamp = Temporal.Now.instant().toZonedDateTimeISO("UTC").startOfDay().with({ day: 1 });
        this.toTimestamp = this.fromTimestamp.add({ months: 3 });

        this.monthsContainers = [];
        this.monthsLabels = [];
        this.months = [];

        this.renderers = { torn_event: this.renderTornEvent };
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name != "hidden") {
            return;
        } else if (this.hidden) {
            return;
        }

        this.startRender();
    }

    connectedCallback() {
        this.buildContainer();
        this.attachControls();
    }

    buildContainer() {
        for (let monthIndex = 0; monthIndex < CALENDAR_GRID_MONTHS_RENDER; monthIndex++) {
            const monthContainer = document.createElement("div");
            monthContainer.classList.add("calendar-grid-month-container", "col-sm-12", "col-lg-4", "p-2");
            this.monthsContainers.push(monthContainer);
            this.append(monthContainer);

            const monthLabel = document.createElement("label");
            monthLabel.classList.add("calendar-grid-month-label");
            monthLabel.textContent = "N/A";
            this.monthsLabels.push(monthLabel);
            monthContainer.append(monthLabel);

            const month = document.createElement("calendar-grid-month");
            month.classList.add("m-3");
            this.months.push(month);
            monthContainer.append(month);
        }

        this.renderEmptyMonths();
    }

    renderEmptyMonths() {
        for (let monthIndex = 0; monthIndex < CALENDAR_GRID_MONTHS_RENDER; monthIndex++) {
            this.renderEmptyMonth(monthIndex);
        }
    }

    renderEmptyMonth(monthIndex) {
        const timestamp = this.fromTimestamp.add({ months: monthIndex });
        const monthLabel = this.monthsLabels[monthIndex];
        const monthGrid = this.months[monthIndex];

        monthGrid.innerHTML = "";

        const monthName = timestamp.toLocaleString("en-US", { month: "long" });
        monthLabel.textContent = `${monthName} ${timestamp.year}`;

        // We want to determine what day the week starts on. We are going to use an American
        // style calendar where the week starts on Sunday.
        const startDayOfWeek = timestamp.dayOfWeek === 7 ? 0 : timestamp.dayOfWeek;

        for (let dayIndex = 1, currentWeek = 1; dayIndex <= timestamp.daysInMonth; dayIndex++) {
            const currentDayTimestamp = timestamp.with({ day: dayIndex });
            const dayOfWeek = currentDayTimestamp.dayOfWeek === 7 ? 0 : currentDayTimestamp.dayOfWeek;

            this.renderEmptyDay(monthGrid, currentDayTimestamp, dayOfWeek, currentWeek);

            if (dayOfWeek === 6) {
                currentWeek++;
            }
        }
    }

    renderEmptyDay(monthGrid, currentDayTimestamp, dayOfWeek, currentWeek) {
        const dayCell = document.createElement("calendar-grid-day");
        dayCell.style.gridColumn = dayOfWeek + 1;
        dayCell.style.gridRow = currentWeek;
        dayCell.setAttribute("data-date", currentDayTimestamp.toPlainDate().toString());
        monthGrid.append(dayCell);

        const dayCellLabel = document.createElement("label");
        dayCellLabel.classList.add("calendar-grid-day-label");
        dayCellLabel.textContent = currentDayTimestamp.day;
        dayCell.append(dayCellLabel);
    }

    attachControls() {
        const previousMonthButton = document.getElementById("calendar-grid-previous");
        const nextMonthButton = document.getElementById("calendar-grid-next");

        previousMonthButton.addEventListener("click", () => {
            this.fromTimestamp = this.fromTimestamp.add({ months: -1 });
            this.toTimestamp = this.toTimestamp.add({ months: -1 });

            this.startRender();
        });
        nextMonthButton.addEventListener("click", () => {
            this.fromTimestamp = this.fromTimestamp.add({ months: 1 });
            this.toTimestamp = this.toTimestamp.add({ months: 1 });

            this.startRender();
        });
    }

    startRender() {
        tfetch(
            "GET",
            `faction/${factionID}/calendar?from=${this.fromTimestamp.epochMilliseconds / 1000}&to=${this.toTimestamp.epochMilliseconds / 1000}`,
            {
                errorTitle: "Failed to Load Calendar",
            },
        ).then(this.render.bind(this));
    }

    render(eventsData) {
        eventsData.forEach((event) => {
            const renderer = this.renderers[event.category];

            if (renderer == null) {
                console.error(`Invalid event category ${event.category}`);
            } else {
                renderer.bind(this)(event);
            }
        });
    }

    renderTornEvent(eventData) {
        const start = Temporal.Instant.fromEpochSeconds(eventData.starts_at).toZonedDateTimeISO("UTC");
        const end = Temporal.Instant.fromEpochSeconds(eventData.ends_at).toZonedDateTimeISO("UTC");
        const durationDays = start.until(end, { largestUnit: "days" }).days;
    }

    renderSingleDayEvent(normalizedEventData) {}

    renderMultiDayEvent(normalizedEventData) {}

    renderMultiWeekEvent(normalizedEventData) {}
}

customElements.define("calendar-grid", CalendarGrid);

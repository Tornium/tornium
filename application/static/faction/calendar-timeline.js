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

class CalendarTimeline extends HTMLElement {
    static observedAttributes = ["hidden"];

    constructor() {
        super();

        this.leftTrack = null;
        this.rightTrack = null;
        this.axis = null;

        // Current page: by default, this is from now to 90 days (~3 months) in the future
        this.fromTimestamp = Temporal.Now.instant().toZonedDateTimeISO("UTC").startOfDay().toInstant();
        this.toTimestamp = Temporal.Now.instant().toZonedDateTimeISO("UTC").startOfDay().add({ days: 90 }).toInstant();
        this.pixelsPerDay = 25;

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
        this.leftTrack = document.createElement("calendar-timeline-track");
        this.leftTrack.id = "calendar-timeline-timeline-track-left";
        this.append(this.leftTrack);

        this.axis = document.createElement("calendar-timeline-axis");
        this.append(this.axis);

        this.rightTrack = document.createElement("calendar-timeline-track");
        this.rightTrack.id = "calendar-timeline-timeline-track-right";
        this.append(this.rightTrack);
    }

    attachControls() {
        this.addEventListener("wheel", this.handleWheel.bind(this), { passive: false });

        const zoomInButton = document.getElementById("calendar-timeline-zoom-in");
        const zoomOutButton = document.getElementById("calendar-timeline-zoom-out");
        const panPastButton = document.getElementById("calendar-timeline-pan-past");
        const panFutureButton = document.getElementById("calendar-timeline-pan-future");

        zoomInButton.addEventListener("click", () => {
            this.applyZoom(1.2);
        });
        zoomOutButton.addEventListener("click", () => {
            this.applyZoom(0.8);
        });
        // FIXME: this.applyPan needs to change by the zoom amount
        panPastButton.addEventListener("click", () => {
            this.applyPan(-7);
        });
        panFutureButton.addEventListener("click", () => {
            this.applyPan(7);
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
        this.leftTrack.innerHTML = "";
        this.rightTrack.innerHTML = "";
        this.axis.innerHTML = "";

        this.updateTimelineScale();

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
        // We should force all Torn events to be on the right side for ease of reading it.
        const eventElement = document.createElement("timeline-period");
        eventElement.initializeTornEvent(eventData);

        const secondsPerDay = 86400;
        const secondsPerHalfDay = 43200;
        const pixelsPerSecond = this.pixelsPerDay / secondsPerDay;
        const fromSecond = this.fromTimestamp.epochMilliseconds / 1000;

        // We want to snap to the nearest half-day as exact positioning is not useful
        const startSecond = Math.round(eventData.starts_at / secondsPerHalfDay) * secondsPerHalfDay;
        let endSecond = Math.round(eventData.ends_at / secondsPerHalfDay) * secondsPerHalfDay;

        if (startSecond == endSecond) {
            endSecond += secondsPerHalfDay;
        }

        const topPosition = (startSecond - fromSecond) * pixelsPerSecond;
        const height = Math.max((endSecond - startSecond) * pixelsPerSecond, 30);

        eventElement.style.top = `${topPosition}px`;
        eventElement.style.height = `${height}px`;

        this.leftTrack.append(eventElement);
    }

    updateTimelineScale() {
        // Since zooming and panning the timeline affects the to and from timestamps of the
        // state of the timeline, we need to adjust that before re-rendering.

        // Sets the internal height of the grid so it can actually be scrolled
        const totalDays = (this.toTimestamp.epochMilliseconds - this.fromTimestamp.epochMilliseconds) / 86400 / 1000;
        const totalHeight = totalDays * this.pixelsPerDay;
    }

    updateVisualPositions() {
        const secondsPerDay = 86400;
        const pixelsPerSecond = this.pixelsPerDay / secondsPerDay;
        const fromSecond = this.fromTimestamp.epochMilliseconds / 1000;

        const allEvents = this.querySelectorAll(".timeline-event-period");
        allEvents.forEach((el) => {
            const start = parseFloat(el.dataset.start);
            const end = parseFloat(el.dataset.end);

            const newTop = (start - fromSecond) * pixelsPerSecond;
            let newHeight = (end - start) * pixelsPerSecond;

            newHeight = Math.max(newHeight, 30);

            el.style.top = `${newTop}px`;
            el.style.height = `${newHeight}px`;
        });
    }

    applyZoom(zoomFactor) {
        this.pixelsPerDay = Math.max(20, Math.min(this.pixelsPerDay * zoomFactor, 500));
        this.updateTimelineScale();
        this.updateVisualPositions();
        this.startRender();
    }

    applyPan(daysOffset) {
        const hoursOffset = daysOffset * 24;
        this.fromTimestamp = this.fromTimestamp.add({ hours: hoursOffset });
        this.toTimestamp = this.toTimestamp.add({ hours: hoursOffset });
        this.startRender();
    }

    handleWheel(event) {
        event.preventDefault();

        if (event.ctrlKey) {
            const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
            debounce(() => {
                this.applyZoom(zoomFactor);
            }, 500)();

            return;
        }

        const secondsPerDay = 86400;
        const pixelsPerSecond = this.pixelsPerDay / secondsPerDay;
        const secondsToPan = Math.round(event.deltaY / pixelsPerSecond);

        // 2. Adjust timestamps instantly
        this.fromTimestamp = this.fromTimestamp.add({ seconds: secondsToPan });
        this.toTimestamp = this.toTimestamp.add({ seconds: secondsToPan });

        // 3. Move blocks on screen smoothly in real-time
        this.updateVisualPositions();

        debounce(() => {
            this.startRender();
        }, 500)();
    }
}

class TimelinePeriod extends HTMLElement {
    constructor() {
        super();

        this.guid = null;
        this.name = null;
        this.description = null;
        this.startTimestamp = null;
        this.endTimestamp = null;
        this.configurable = null;
    }

    connectedCallback() {}

    initializeTornEvent(eventData) {
        this.guid = eventData.guid;
        this.name = eventData.title;
        this.description = eventData.description;
        this.startTimestamp = Temporal.Instant.fromEpochMilliseconds(eventData.starts_at * 1000);
        this.endTimestamp = Temporal.Instant.fromEpochMilliseconds(eventData.ends_at * 1000);
        this.configurable = eventData.configurable;

        this.render();
    }

    render() {
        this.classList.add("timeline-event-period");

        const label = document.createElement("label");
        label.innerText = this.name;
        this.append(label);
    }
}

class TimelineEvent extends HTMLElement {
    constructor() {
        super();
    }

    connectedCallback() {}
}

customElements.define("calendar-timeline", CalendarTimeline);
customElements.define("timeline-period", TimelinePeriod);
customElements.define("timeline-event", TimelineEvent);

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

class DateTimeInput extends HTMLElement {
    constructor() {
        super();

        this.fieldset = null;
        this.yearInput = null;
        this.monthInput = null;
        this.dayInput = null;
        this.hourInput = null;
        this.minuteInput = null;
    }

    connectedCallback() {
        this.buildContainer();
        this.addEventListeners();
    }

    buildContainer() {
        if (this.fieldset != null) {
            return;
        }

        this.fieldset = document.createElement("fieldset");
        this.fieldset.classList.add("datetime-fieldset");
        this.append(this.fieldset);

        const legend = document.createElement("legend");
        legend.classList.add("datetime-legend");
        legend.innerText = this.getAttribute("data-legend");
        this.fieldset.append(legend);

        this.buildDateContainer();
        this.buildTimeContainer();
    }

    buildDateContainer() {
        if (this.fieldset === null) {
            return;
        }

        const dateContainer = document.createElement("div");
        dateContainer.classList.add("datetime-group", "datetime-group-date");
        this.fieldset.append(dateContainer);

        const yearInputLabel = document.createElement("label");
        dateContainer.append(yearInputLabel);

        const yearInputLabelText = document.createElement("span");
        yearInputLabelText.classList.add("label-text");
        yearInputLabelText.innerText = "Year";
        yearInputLabel.append(yearInputLabelText);

        this.yearInput = document.createElement("input");
        this.yearInput.setAttribute("type", "text");
        this.yearInput.setAttribute("inputmode", "numeric");
        this.yearInput.setAttribute("placeholder", "YYYY");
        this.yearInput.setAttribute("pattern", "[0-9]{1,4}");
        this.yearInput.setAttribute("maxlength", 4);
        this.yearInput.setAttribute("required", "");
        yearInputLabel.append(this.yearInput);
        this.insertSeperator(dateContainer);

        const monthInputLabel = document.createElement("label");
        dateContainer.append(monthInputLabel);

        const monthInputLabelText = document.createElement("span");
        monthInputLabelText.classList.add("label-text");
        monthInputLabelText.innerText = "Month";
        monthInputLabel.append(monthInputLabelText);

        this.monthInput = document.createElement("input");
        this.monthInput.setAttribute("type", "text");
        this.monthInput.setAttribute("inputmode", "numeric");
        this.monthInput.setAttribute("placeholder", "MM");
        this.monthInput.setAttribute("pattern", "[0-9]{1,2}");
        this.monthInput.setAttribute("maxlength", 2);
        this.monthInput.setAttribute("required", "");
        monthInputLabel.append(this.monthInput);
        this.insertSeperator(dateContainer);

        const dayInputLabel = document.createElement("label");
        dateContainer.append(dayInputLabel);

        const dayInputLabelText = document.createElement("span");
        dayInputLabelText.classList.add("label-text");
        dayInputLabelText.innerText = "Day";
        dayInputLabel.append(dayInputLabelText);

        this.dayInput = document.createElement("input");
        this.dayInput.setAttribute("type", "text");
        this.dayInput.setAttribute("inputmode", "numeric");
        this.dayInput.setAttribute("placeholder", "DD");
        this.dayInput.setAttribute("pattern", "[0-9]{1,2}");
        this.dayInput.setAttribute("maxlength", 2);
        this.dayInput.setAttribute("required", "");
        dayInputLabel.append(this.dayInput);
    }

    buildTimeContainer() {
        if (this.fieldset === null) {
            return;
        }

        const timeContainer = document.createElement("div");
        timeContainer.classList.add("datetime-group", "datetime-group-time", "mt-2", "mt-md-0");
        this.fieldset.append(timeContainer);

        const hourInputLabel = document.createElement("label");
        timeContainer.append(hourInputLabel);

        const hourInputLabelText = document.createElement("span");
        hourInputLabelText.classList.add("label-text");
        hourInputLabelText.innerText = "Hour";
        hourInputLabel.append(hourInputLabelText);

        this.hourInput = document.createElement("input");
        this.hourInput.setAttribute("type", "text");
        this.hourInput.setAttribute("inputmode", "numeric");
        this.hourInput.setAttribute("placeholder", "HH");
        this.hourInput.setAttribute("pattern", "[0-9]{1,2}");
        this.hourInput.setAttribute("maxlength", 2);
        this.hourInput.setAttribute("required", "");
        hourInputLabel.append(this.hourInput);
        this.insertSeperator(timeContainer);

        const minuteInputLabel = document.createElement("label");
        timeContainer.append(minuteInputLabel);

        const minuteInputLabelText = document.createElement("span");
        minuteInputLabelText.classList.add("label-text");
        minuteInputLabelText.innerText = "Minute";
        minuteInputLabel.append(minuteInputLabelText);

        this.minuteInput = document.createElement("input");
        this.minuteInput.setAttribute("type", "text");
        this.minuteInput.setAttribute("inputmode", "numeric");
        this.minuteInput.setAttribute("placeholder", "MM");
        this.minuteInput.setAttribute("pattern", "[0-9]{1,2}");
        this.minuteInput.setAttribute("maxlength", 2);
        this.minuteInput.setAttribute("required", "");
        minuteInputLabel.append(this.minuteInput);
    }

    addEventListeners() {
        this.yearInput.addEventListener("input", this);
        this.monthInput.addEventListener("input", this);
        this.dayInput.addEventListener("input", this);
        this.hourInput.addEventListener("input", this);
        this.minuteInput.addEventListener("input", this);
    }

    insertSeperator(container) {
        const seperator = document.createElement("span");
        seperator.classList.add("datetime-group-seperator");
        seperator.innerText = "|";
        container.append(seperator);
    }

    get value() {
        if (
            this.yearInput.value == null &&
            this.monthInput.value == null &&
            this.dayInput.value == null &&
            this.hourInput.value == null &&
            this.minuteInput == null
        ) {
            // We want to return a distinct value when nothing is set in the element versus an invalid state.
            return null;
        }

        const year = parseInt(this.yearInput.value);
        const month = parseInt(this.monthInput.value);
        const day = parseInt(this.dayInput.value);
        const hour = parseInt(this.hourInput.value);
        const minute = parseInt(this.minuteInput.value);

        // TODO: Add validity errors to the individual inputs

        if (isNaN(year) || Math.floor(year / 1000) != 2) {
            return undefined;
        } else if (isNaN(month) || month < 1 || month > 12) {
            return undefined;
        } else if (isNaN(day) || day > 31 || day < 1) {
            return undefined;
        } else if (isNaN(hour) || hour > 23 || hour < 0) {
            return undefined;
        } else if (isNaN(minute) || minute < 0 || minute > 59) {
            return undefined;
        }

        const datetime = new Date(year, month - 1, day, hour, minute, 0);
        return Math.floor(datetime.getTime() / 1000);
    }

    // TODO: Add set value

    handleEvent(event) {
        this[`on${event.type}`](event);
    }

    oninput(event) {
        // TODO: Debounce the input
        // The existing debounce function does not work properly
        // FIXME: The data gets refreshed when exiting the individual inputs in the element

        if (this.value === undefined) {
            // We don't need to send excessive events for changes to the datetime input that result in invalid input.
            return;
        }

        this.dispatchEvent(new Event("change", { bubbles: true }));
    }
}

ready(() => {
    customElements.define("datetime-input", DateTimeInput);
});

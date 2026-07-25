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

class PageSearch extends HTMLElement {
    constructor() {
        super();

        this.pages = [];

        this.backdrop = null;
        this.input = null;
        this.listbox = null;

        this.onInput = debounce(this._onInput.bind(this), 100);
        this.handleKeydown = this._handleKeydown.bind(this);
        this.onFocus = this._onFocus.bind(this);
        this.onDocumentClick = this._onDocumentClick.bind(this);
        this.onDocumentKeyDown = this._onDocumentKeyDown.bind(this);
    }

    connectedCallback() {
        this.parsePages();
        this.buildCombobox();

        this.input.addEventListener("input", this.onInput);
        this.input.addEventListener("keydown", this.handleKeydown);
        this.input.addEventListener("focus", this.onFocus);
        document.addEventListener("click", this.onDocumentClick);
        document.addEventListener("keydown", this.onGlobalKeydown);

        const apiEndpoint = this.getAttribute("data-api-endpoint");
        if (apiEndpoint != null) {
            this.fetchRemote(apiEndpoint);
        }
    }

    disconnectedCallback() {
        document.removeEventListener("click", this.onDocumentClick);
        document.removeEventListener("keydown", this.onDocumentKeyDown);
    }

    parsePages() {
        const domPages = this.querySelectorAll("page-option");
        this.pages = Array.from(domPages).map((page) => ({
            title: page.textContent.trim(),
            href: page.getAttribute("href") || "#",
            icon: page.getAttribute("icon") || null,
            keywords: (page.getAttribute("keywords") || "")
                .split(",")
                .map((keyword) => keyword.trim().toLowerCase())
                .filter(Boolean),
            source: "static",
        }));
    }

    fetchRemote(apiEndpoint) {
        if (apiEndpoint == null) {
            return;
        }

        tfetch("GET", apiEndpoint, {
            errorTitle: "Failed to load dynamic search pages",
        }).then((pageData) => {
            if (!Array.isArray(pageData)) {
                return;
            }

            const existingPageLinks = new Set(this.pages.map((page) => page.href));

            for (const pageEntry of pageData) {
                if (existingPageLinks.has(pageEntry.location)) {
                    continue;
                }

                this.pages.push({
                    title: pageEntry.title,
                    href: pageEntry.location,
                    icon: pageEntry.icon || null,
                    keywords: pageEntry.keywords || [],
                    source: "remote",
                });
            }

            if (this.input.value.trim().length > 0) {
                this.handleInput();
            }
        });
    }

    buildCombobox() {
        this.backdrop = document.createElement("div");
        this.backdrop.classList.add("page-search-backdrop");
        this.backdrop.addEventListener("click", this.close);
        this.append(this.backdrop);

        const wrapper = document.createElement("div");
        wrapper.setAttribute("role", "group");
        wrapper.classList.add("page-search-wrapper");
        this.append(wrapper);

        const label = document.createElement("label");
        // TODO: Add a relation to the input (eg for attribute)
        label.textContent = "Search pages";
        label.classList.add("page-search-label", "visually-hidden");
        wrapper.append(label);

        const inputGroup = document.createElement("div");
        inputGroup.classList.add("input-group", "input-group-sm");
        wrapper.append(inputGroup);

        this.input = document.createElement("input");
        this.input.setAttribute("type", "text");
        this.input.setAttribute("autocomplete", "off");
        this.input.setAttribute("role", "combobox");
        this.input.setAttribute("aria-autocomplete", "list");
        this.input.setAttribute("aria-expanded", "false");
        // this.input.setAttribute("aria-controls", listboxId);
        this.input.setAttribute("aria-activedescendant", "");
        // this.input.setAttribute("aria-labelledby", labelId);
        this.input.setAttribute("placeholder", "Search pages");
        this.input.classList.add("form-control", "page-search-input");
        inputGroup.append(this.input);

        this.listbox = document.createElement("div");
        this.listbox.setAttribute("role", "listbox");
        this.listbox.setAttribute("aria-label", "Search results");
        this.listbox.classList.add("page-search-results", "d-none");
        wrapper.append(this.listbox);
    }

    renderResults(results) {
        this.listbox.innerHTML = "";
        this.input.setAttribute("aria-activedescendant", "");

        if (results.length === 0) {
            const empty = document.createElement("div");
            empty.classList.add("page-search-empty");
            empty.setAttribute("role", "status");
            empty.setAttribute("aria-live", "polite");
            empty.textContent = "No pages found";
            this.listbox.append(empty);
            this.showListbox();
            return;
        }

        results.forEach((page, index) => {
            const item = document.createElement("a");
            item.id = `page-search-option-${index}`;
            item.href = page.href;
            item.setAttribute("role", "option");
            item.setAttribute("aria-selected", "false");
            item.setAttribute("data-index", index);
            item.classList.add("page-search-result-item");
            item.tabIndex = -1;
            item.innerHTML = `<i class="${page.icon} page-search-result-icon" aria-hidden="true"></i>` + page.title;

            item.addEventListener("mouseenter", () => {
                this.setActiveDescendant(index);
            });
            item.addEventListener("click", () => {
                this.close();
            });

            this.listbox.append(item);
        });

        this.announceResultCount(results.length);
        this.showListbox();
    }

    announceResultCount(count) {
        let liveRegion = this.querySelector(".page-search-live-region");
        if (!liveRegion) {
            liveRegion = document.createElement("div");
            liveRegion.classList.add("page-search-live-region", "visually-hidden");
            liveRegion.setAttribute("aria-live", "polite");
            liveRegion.setAttribute("aria-atomic", "true");
            this.append(liveRegion);
        }

        liveRegion.textContent = `${count} result${count === 1 ? "" : "s"} available`;
    }

    setActiveDescendant(index) {
        const options = this.listbox.querySelectorAll("[role='option']");

        options.forEach((option) => {
            option.setAttribute("aria-selected", "false");
            option.classList.remove("active");
        });

        if (index < 0 || index >= options.length) {
            this.activeIndex = -1;
            this.input.setAttribute("aria-activedescendant", "");
            return;
        }

        this.activeIndex = index;
        const activeOption = options[index];
        activeOption.setAttribute("aria-selected", "true");
        activeOption.classList.add("active");
        activeOption.scrollIntoView({ block: "nearest" });
        this.input.setAttribute("aria-activedescendant", activeOption.id);
    }

    showListbox() {
        this.listbox.classList.remove("d-none");
        this.input.setAttribute("aria-expanded", "true");
    }

    search(query) {
        const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);

        if (terms.length === 0) {
            return [];
        }

        return this.pages.filter((page) => {
            const haystack = [page.title.toLowerCase(), ...page.keywords].join(" ");
            return terms.every((term) => haystack.includes(term));
        });
    }

    close() {
        this.hide();
        this.classList.remove("page-search-open");
        this.input.blur();
    }

    hide() {
        this.listbox.classList.add("d-none");
        this.input.setAttribute("aria-expanded", "false");
        this.input.setAttribute("aria-activedescendant", "");
        this.activeIndex = -1;

        this.listbox.querySelectorAll("[role='option']").forEach((option) => {
            option.setAttribute("aria-selected", "false");
            option.classList.remove("active");
        });
    }

    _onInput() {
        const query = this.input.value;

        if (query.trim().length === 0) {
            this.hide();
            return;
        }

        const results = this.search(query);
        this.renderResults(results);
    }

    _handleKeydown(event) {
        const options = this.listbox.querySelectorAll("[role='option']");
        const isExpanded = this.input.getAttribute("aria-expanded") === "true";
        console.log(event);
        console.log(options);
        console.log(isExpanded);

        switch (event.key) {
            case "ArrowDown":
                event.preventDefault();
                if (!isExpanded) {
                    if (this.input.value.trim().length > 0) {
                        this.handleInput();
                    }
                    return;
                }
                this.setActiveDescendant(this.activeIndex < options.length - 1 ? this.activeIndex + 1 : 0);
                break;

            case "ArrowUp":
                event.preventDefault();
                if (!isExpanded) return;
                this.setActiveDescendant(this.activeIndex > 0 ? this.activeIndex - 1 : options.length - 1);
                break;

            case "Enter":
                if (!isExpanded) return;
                event.preventDefault();
                if (this.activeIndex >= 0 && options[this.activeIndex]) {
                    window.location.href = options[this.activeIndex].href;
                }
                break;

            case "Escape":
                event.preventDefault();
                event.stopPropagation();
                this.close();
                break;

            case "Home":
                if (isExpanded && options.length > 0) {
                    event.preventDefault();
                    this.setActiveDescendant(0);
                }
                break;

            case "End":
                if (isExpanded && options.length > 0) {
                    event.preventDefault();
                    this.setActiveDescendant(options.length - 1);
                }
                break;

            case "Tab":
                if (isExpanded) {
                    this.close();
                }
                break;
        }
    }

    _onFocus(event) {
        this.classList.add("page-search-open");

        if (this.input.value.trim().length == 0) {
            return;
        }

        this.onInput();
    }

    _onDocumentClick(event) {
        if (this.contains(event.target)) {
            return;
        }

        this.close();
    }

    _onDocumentKeyDown(event) {
        if ((event.ctrlKey || event.metaKey) && event.key === "k") {
            event.preventDefault();
            this.classList.add("page-search-open");
            this.input.focus();
        }
    }
}

ready(() => {
    customElements.define("page-search", PageSearch);
});

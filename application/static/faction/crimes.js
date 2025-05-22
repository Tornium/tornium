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

function addTeamSelector({ current_crime: current_crime, guid: guid, members: members, name: name, oc_name: oc_name }) {
    const container = document.getElementById("team-list");

    const team = document.createElement("li");
    team.classList.add("list-group-item", "d-flex");
    container.appendChild(team);

    const teamSelector = document.createElement("input");
    teamSelector.setAttribute("type", "radio");
    teamSelector.setAttribute("name", "team-selector");
    teamSelector.setAttribute("data-team-guid", guid);
    teamSelector.addEventListener("change", loadViewer);
    team.appendChild(teamSelector);

    const teamDescription = document.createElement("p");
    teamDescription.classList.add("card-text", "px-3");
    teamDescription.setAttribute("style", "width: 100%"); // TODO: Determine if there's a better method of setting the style here
    teamDescription.textContent = `${oc_name}:`;
    team.appendChild(teamDescription);

    const teamMembers = document.createElement("span");
    teamMembers.classList.add("text-secondary", "d-inline-block", "text-truncate");
    teamMembers.setAttribute("style", "width: inherit"); // TODO: Determine if there's a better method of setting the style here
    // FIXME: Use the usernames of the members or skip if not set
    // TODO: Add icon flagging OC teams with not enough members
    teamMembers.textContent = members.length == 0 ? "None" : members.join(", ");
    teamDescription.appendChild(teamMembers);
}

function loadViewerTeam({members: members, name: name, oc_name: oc_name}) {
    const viewerTitle = document.getElementById("viewer-title");
    viewerTitle.textContent = `Team Viewer: ${name} [${oc_name}]`;

    const viewer = document.getElementById("viewer");
    viewer.innerHTML = "";

    const viewerMembers = document.createElement("div");
    viewerMembers.classList.add("card");
    viewer.appendChild(viewerMembers);

    const viewerMembersHeader = document.createElement("div");
    viewerMembersHeader.classList.add("card-header");
    viewerMembersHeader.textContent = "Team Members";
    viewerMembers.appendChild(viewerMembersHeader);

    const viewerMembersList = document.createElement("ul");
    viewerMembersList.classList.add("list-group", "list-group-flush", "list-group-numbered");
    viewerMembers.appendChild(viewerMembersList);

    members.forEach(({guid, slot_type, slot_index}) => {
        const viewerMemberChild = document.createElement("li");
        viewerMemberChild.classList.add("list-group-item", "d-flex", "flex-fill", "align-items-center");
        viewerMembersList.appendChild(viewerMemberChild);

        const memberTitle = document.createElement("div");
        memberTitle.classList.add("fw-bold");
        memberTitle.textContent = `[${slot_type} ${slot_index}]`;
        viewerMemberChild.appendChild(memberTitle);

        const memberSelector = document.createElement("select");
        memberSelector.classList.add("team-member-selector", "ms-0", "ms-md-3");
        memberSelector.setAttribute("data-team-member-guid", guid);
        viewerMemberChild.appendChild(memberSelector);
        new TomSelect(memberSelector, {
            create: false,
            preload: "focus",
            load: function(query, callback) {
                if (this.loading > 1) {
                    // Blocks loading this more than once.
                    // The data shouldn't change between keypresses and can be filtered on the client
                    callback();
                    return;
                }

                tfetch("GET", `faction/${factionID}/crime/cpr/${oc_name}/${slot_type}`, {
                    errorTitle: "Member CPR Load Failed"
                }).then((data) => {
                    callback(data);
                    this.settings.load = null;
                });
            },
            render: {
                loading: null,
            }
        });
        // TODO: Add member selection and updating via API
    });

    const viewerStats = document.createElement("div");
    viewerStats.classList.add("card", "mt-3");
    viewer.appendChild(viewerStats);

    const viewerStatsHeader = document.createElement("div");
    viewerStatsHeader.classList.add("card-header");
    viewerStatsHeader.textContent = "Team Statistics";
    viewerStats.appendChild(viewerStatsHeader);

    // TODO: Have OC team members pre-initialized
}

function loadViewer(event) {
    const teamGUID = this.getAttribute("data-team-guid");

    tfetch("GET", `faction/${factionID}/crime/team/${teamGUID}`, {
        errorTitle: "Team Retrieval Failed",
        errorHandler: (jsonError) => {
            // TODO: Update error handler
            console.log(jsonError);
        },
    }).then((data) => {
        loadViewerTeam(data);
    });
}

function clearViewer() {
    const viewer = document.getElementById("viewer");
    viewer.innerHTML = "";

    const defaultViewer = document.createElement("p");
    defaultViewer.classList.add("card-text");
    defaultViewer.setAttribute("id", "viewer-default");
    defaultViewer.textContent = "Select a team first.";
    viewer.appendChild(defaultViewer);

    document.getElementById("viewer-title").textContent = "Team Viewer";
}

function createTeam(event) {
    const crimeName = document.getElementById("new-oc-selector").value;

    tfetch("POST", `faction/${factionID}/crime/team/${crimeName}`, {
        body: {},
        errorTitle: "Team Creation Failed",
        errorHandler: (jsonError) => {
            // TODO: Update error handler
            console.log(jsonError);
        },
    }).then((data) => {
        generateToast("Team Created Successfully", "The OC team has been successfully created.");
        addTeamSelector(data);
        loadViewerTeam(data);
        // TODO: Select the OC team in the selector
    });
}

ready(() => {
    clearViewer();

    ocNamesRequest().then(() => {
        document.querySelectorAll(".oc-name-selector").forEach((element) => {
            new TomSelect(element, {
                create: false,
            });
        });
    });

    document.getElementById("new-team-button").addEventListener("click", createTeam);
    document.querySelectorAll(`input[name="team-selector"]`).forEach((teamRadioButton) => {
        teamRadioButton.addEventListener("change", loadViewer);
    });
});

<!-- TODO: Bind prev and next page buttons -->

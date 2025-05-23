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

let prevPageButton;
let nextPageButton;
const OFFSET = 10;
let page = 0;

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
    teamDescription.setAttribute("style", "width: 100%");
    teamDescription.textContent = `${oc_name}:`;
    team.appendChild(teamDescription);

    const teamMembers = document.createElement("span");
    teamMembers.classList.add("text-secondary", "d-inline-block", "text-truncate");
    teamMembers.setAttribute("style", "width: inherit");
    // TODO: Add icon flagging OC teams with not enough members

    if (
        members.every((member) => {
            return member.user == null;
        })
    ) {
        teamMembers.textContent = "No Members Set";
    } else {
        let setMembers = [];
        members.forEach((member) => {
            if (member.user != null) {
                setMembers.push(member.user.name);
            }
        });

        teamMembers.textContent = setMembers.join(", ");
    }

    teamDescription.appendChild(teamMembers);
}

function clearTeamSelector() {
    document.getElementById("team-list").innerHTML = "";
}

function loadTeamSelectorPage(pageLoaded) {
    tfetch("GET", `faction/${factionID}/crime/team?limit=10&offset=${pageLoaded * OFFSET}`, {
        errorTitle: "Member CPR Load Failed",
    }).then((data) => {
        clearTeamSelector();
        data.forEach((team) => {
            addTeamSelector(team);
        });

        if (data.length < OFFSET) {
            nextPageButton.setAttribute("disabled", "");
        }
    });

    page = pageLoaded;
    prevPageButton.removeAttribute("disabled");
    nextPageButton.removeAttribute("disabled");

    if (page == 0) {
        prevPageButton.setAttribute("disabled", "");
    }
}

function loadViewerTeam({ guid: guid, members: members, name: name, oc_name: oc_name }) {
    const viewerTitle = document.getElementById("viewer-title");
    viewerTitle.textContent = `Team Viewer: ${name} [${oc_name}]`;
    // TODO: Convert the OC name to an input

    const viewer = document.getElementById("viewer");
    viewer.setAttribute("data-team-guid", guid);
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

    members.forEach(({ guid: guid, slot_type: slot_type, slot_index: slot_index, user: user }) => {
        const viewerMemberChild = document.createElement("li");
        viewerMemberChild.classList.add("list-group-item", "d-flex", "flex-wrap", "flex-fill", "align-items-center");
        viewerMembersList.appendChild(viewerMemberChild);

        const memberTitle = document.createElement("div");
        memberTitle.classList.add("fw-bold");
        memberTitle.textContent = `[${slot_type} ${slot_index}]`;
        viewerMemberChild.appendChild(memberTitle);

        const memberSelector = document.createElement("select");
        memberSelector.classList.add("team-member-selector", "ms-0", "ms-md-3");
        memberSelector.setAttribute("data-team-member-guid", guid);
        memberSelector.addEventListener("change", updateTeamMember);
        viewerMemberChild.appendChild(memberSelector);

        // TODO: Align tomselects vertically
        new TomSelect(memberSelector, {
            create: false,
            preload: true,
            valueField: "value",
            labelField: "label",
            sortField: [{ field: "$cpr" }, { field: "$score" }],
            options: user == null ? [] : [{ value: user.tid, label: `${user.name} [${user.cpr}%]` }],
            items: user == null ? [] : [user.tid],
            load: function (query, callback) {
                if (this.loading > 1) {
                    // Blocks loading this more than once.
                    // The data shouldn't change between keypresses and can be filtered on the client
                    callback();
                    return;
                }

                tfetch("GET", `faction/${factionID}/crime/cpr/${oc_name}/${slot_type}`, {
                    errorTitle: "Member CPR Load Failed",
                })
                    .then((data) => {
                        callback(
                            Object.entries(data).map(([key, value]) => ({
                                value: key,
                                label: `${value.name} [${value.cpr}%]`,
                                cpr: value.cpr,
                            })),
                        );
                        this.settings.load = null;
                    })
                    .catch(() => {
                        callback();
                    });
            },
            render: {
                loading: null,
            },
        });
    });

    const viewerStats = document.createElement("div");
    viewerStats.classList.add("card", "mt-3");
    viewer.appendChild(viewerStats);

    const viewerStatsHeader = document.createElement("div");
    viewerStatsHeader.classList.add("card-header");
    viewerStatsHeader.textContent = "Team Statistics";
    viewerStats.appendChild(viewerStatsHeader);
}

function updateTeamMember(event) {
    const memberGUID = this.getAttribute("data-team-member-guid");
    const teamGUID = document.getElementById("viewer").getAttribute("data-team-guid");
    const selectedMember = this.options[this.selectedIndex].value;

    tfetch("PUT", `faction/${factionID}/crime/team/${teamGUID}/member/${memberGUID}/${selectedMember}`, {
        errorHandler: (jsonError) => {
            let errorBody = `[${jsonError.code}] ${jsonError.message}`;
            if (jsonError.details.message != null) {
                errorBody += " " + jsonError.details.message;
            }

            generateToast("Team Member Set Failed", errorBody);
        },
    }).then((data) => {
        // TODO: Handle response data
    });
}

function loadViewer(event) {
    const teamGUID = this.getAttribute("data-team-guid");

    tfetch("GET", `faction/${factionID}/crime/team/${teamGUID}`, {
        errorTitle: "Team Retrieval Failed",
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
        errorTitle: "Team Creation Failed",
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

    prevPageButton = document.getElementById("team-prev-page");
    nextPageButton = document.getElementById("team-next-page");
    prevPageButton.addEventListener("click", (event) => {
        loadTeamSelectorPage(page - 1);
    });
    nextPageButton.addEventListener("click", (event) => {
        loadTeamSelectorPage(page + 1);
    });
});

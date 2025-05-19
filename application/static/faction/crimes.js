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
    teamMembers.textContent = members.length == 0 ? "None" : members.join(", ");
    teamDescription.appendChild(teamMembers);
}

function loadViewerTeam(teamData) {
    console.log(teamData);
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
        generateToast("Team Retrieval Successful", "The OC team has been successfully retrieved.");
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
    document.querySelectorAll(`input[name="team-selector"]`).addEventListener("change", loadViewer);
});

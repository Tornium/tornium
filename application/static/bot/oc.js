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

function setToolChannel(event) {
    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/tool/channel`, {
        body: { channel: this.options[this.selectedIndex].value },
        errorTitle: "OC Tool Channel Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Channel Set Successful",
            "The channel for OC missing tool notifications has been successfully set.",
        );
    });
}

function setToolRoles(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedRoles = [];

    selectedOptions.forEach((element) => {
        selectedRoles.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/tool/roles`, {
        body: { roles: selectedRoles },
        errorTitle: "OC Tool Roles Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Roles Set Successful",
            "The roles for OC missing tool notifications have been successfully set.",
        );
    });
}

function setToolCrimes(event) {
    const selectedOptions = this.querySelectorAll(":checked");
    let selectedCrimes = [];

    selectedOptions.forEach((element) => {
        selectedCrimes.push(element.getAttribute("value"));
    });

    tfetch("POST", `bot/${guildid}/crimes/${this.getAttribute("data-faction")}/tool/crimes`, {
        body: { crimes: selectedCrimes },
        errorTitle: "OC Tool Crimes Set Failed",
    }).then(() => {
        generateToast(
            "OC Tool Crimes Set Successful",
            "The crimes for OC missing tool notifications have been successfully set.",
        );
    });
}

ready(() => {
    const channelsPromise = channelsRequest();
    const rolesPromise = rolesRequest();

    channelsPromise
        .then(() => {
            document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                let channelID = element.getAttribute("data-selected-channel");
                channelID = channelID == "none" ? "0" : channelID;
                const options = element.querySelectorAll(`option[value="${channelID}"]`);

                if (options.length !== 1) {
                    return;
                }

                options[0].setAttribute("selected", "");
            });
        })
        .finally(() => {
            document.querySelectorAll(".discord-channel-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    rolesPromise
        .then(() => {
            document.querySelectorAll(".discord-role-selector").forEach((element) => {
                let roles = parseIntArray(element.getAttribute("data-selected-roles"));

                roles.forEach((roleID) => {
                    const options = element.querySelectorAll(`option[value="${roleID}"]`);

                    if (options.length !== 1) {
                        return;
                    }

                    options[0].setAttribute("selected", "");
                });
            });
        })
        .finally(() => {
            document.querySelectorAll(".discord-role-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    ocNamesRequest()
        .then(() => {
            document.querySelectorAll(".oc-name-selector").forEach((element) => {
                const crimes = parseStringArray(element.getAttribute("data-selected-crimes"));
                console.log(crimes);

                crimes.forEach((crimeName) => {
                    const options = element.querySelectorAll(`option[value="${crimeName}"]`);

                    if (options.length !== 1) {
                        return;
                    }

                    options[0].setAttribute("selected", "");
                });
            });
        })
        .finally(() => {
            document.querySelectorAll(".oc-name-selector").forEach((element) => {
                new TomSelect(element, {
                    create: false,
                });
            });
        });

    document.querySelectorAll(".oc-tool-channel").forEach((element) => {
        element.addEventListener("change", setToolChannel);
    });
    document.querySelectorAll(".oc-tool-roles").forEach((element) => {
        element.addEventListener("change", setToolRoles);
    });
    document.querySelectorAll(".oc-tool-crimes").forEach((element) => {
        element.addEventListener("change", setToolCrimes);
    });
});

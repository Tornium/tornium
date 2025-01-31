/* Copyright (C) 2021-2023 tiksan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>. */

$(document).ready(function () {
    let chainConfig = null;
    let channels = null;

    if (guildid === "0") {
        generateToast(
            "Faction Guild Not Set",
            "No Discord server was set for this faction. Please set this before moving on.",
        );
        throw new Error("Faction guild error");
    }

    let chainPromise = tfetch("GET", "faction/chain", { errorTitle: "Chain OD Config Not Located" });
    let channelsPromise = channelsRequest();

    Promise.all([chainPromise, channelsPromise]).then((response) => {
        chainConfig = response[0];

        let odChannel = $(`#od-channel option[value="${chainConfig.od.channel}"]`);

        if (odChannel.length !== 0) {
            odChannel.attr("selected", "");
        }

        document.querySelectorAll(".discord-channel-selector").forEach((element) => {
            new TomSelect(element, {
                create: false,
            });
        });
    });

    $("#od-channel").on("change", function () {
        tfetch("POST", "faction/chain/od/channel", {
            body: { channel: this.options[this.selectedIndex].value },
            errorTitle: "OD Channel Set Failed",
        }).then(() => {
            generateToast("OD Channel Set Successful");
        });
    });
});

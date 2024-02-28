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

const guildid = document.currentScript.getAttribute("data-guildid");

$(document).ready(function () {
    let chainConfig = null;
    let channels = null;

    if (guildid === "0") {
        generateToast(
            "Faction Guild Not Set",
            "No Discord server was set for this faction. Please set this before moving on."
        );
        throw new Error("Faction guild error");
    }

    let chainPromise = tfetch("GET", "faction/chain", { errorTitle: "Chain OD Config Not Located" });
    let channelsPromise = channelsRequest();

    Promise.all([chainPromise, channelsPromise]).then((response) => {
        chainConfig = response[0];
        channels = response[1];

        $.each(channels, function (category_id, category) {
            let optgroup = $("<optgroup>", {
                label: category["name"],
            });

            $("#od-channel").append(optgroup);

            $.each(category["channels"], function (channel_id, channel) {
                if (chainConfig["od"]["channel"] === parseInt(channel.id)) {
                    optgroup.append($(`<option value="${channel.id}" selected>#${channel.name}</option>`));
                } else {
                    optgroup.append($(`<option value="${channel.id}">#${channel.name}</option>`));
                }
            });
        });

        $(".discord-channel-selector").selectpicker();
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

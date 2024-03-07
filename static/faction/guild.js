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

function addAssistsFaction() {
    tfetch("DELETE", `faction/assists/server/${$("#assist-server-id").value}`, {
        errorTitle: "Failed to remove server",
    }).then(() => {
        window.location.reload();
    });
}

$(document).ready(function () {
    $("#assist-server-id").on("keypress", function (e) {
        if (e.which === 13) {
            addAssistsFaction();
        }
    });
    $("#assist-server-submit").on("click", addAssistsFaction);

    $(".remove-assists-server").on("click", function () {
        const serverSID = this.getAttribute("data-server-sid");

        tfetch("DELETE", `faction/assists/server/${serverSID}`, { errorTitle: "Failed to remove server" }).then(() => {
            window.location.reload();
        });
    });
});

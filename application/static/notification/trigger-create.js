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

ready(() => {
    document.getElementById("trigger-create").addEventListener("click", function (e) {
        let triggerName = document.getElementById("trigger-name").value;
        let triggerDescription = document.getElementById("trigger-description").value;
        let triggerResource = document.getElementById("trigger-resource").value;
        // let triggerOneShot = document.querySelector("input[name=trigger-type]:checked").id == "trigger-one-shot";
        let triggerCron = document.getElementById("trigger-cron").value;
        let triggerCode = document.getElementById("trigger-code").value;

        tfetch("POST", "notification/trigger", {
            body: {
                name: triggerName,
                description: triggerDescription,
                resource: triggerResource,
                // one_shot: triggerOneShot,
                cron: triggerCron,
                code: triggerCode,
            },
            errorHandler: (jsonError) => {
                if(jsonError.code === 0) {
                    generateToast(
                        "Lua Trigger Error",
                        "luac failed to parse this trigger's Lua code",
                        "error"
                    );

                    document.getElementById("lua-error-container").removeAttribute("hidden");
                    document.getElementById("lua-error-text").textContent = jsonError.details.error;
                } else {
                    generateToast(
                        "Trigger Creation Failure",
                        `[${jsonError.code}] ${jsonError.message}`,
                        "error"
                    );
                }
            }
        }).then((response) => {
            window.location.replace("/notification/trigger");
        });
    });
});

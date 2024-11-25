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

let liquidEngine = null;
const templateInput = document.getElementById("trigger-message");
const templateErrorContainer = document.getElementById("liquid-error-container");
const templateErrorText = document.getElementById("liquid-error-text");

function debounce(func, delay) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

function validateTemplate() {
    if (liquidEngine == null) {
        console.error("Liquid engine is not initialized");
        return;
    }

    try {
        liquidEngine.parse(templateInput.value);
    } catch (error) {
        templateErrorContainer.removeAttribute("hidden");
        templateErrorText.textContent = error.message;
        return false;
    }

    // TODO: Validate the variables used in the template

    templateErrorContainer.setAttribute("hidden", "");
    templateErrorText.textContent = "No error loaded...";
    
    return true;
}

function triggerMessageTypeConvert(typeString) {
    switch (typeString) {
        case "trigger-message-update":
            return 0;
        case "trigger-message-send":
            return 1;
        default:
            throw new Exception(`Illegal message type string: ${typeString}`);
    }
}

function createTrigger() {
    // TODO: Make these query selectors constants
    let triggerName = document.getElementById("trigger-name").value;
    let triggerDescription = document.getElementById("trigger-description").value;
    let triggerResource = document.getElementById("trigger-resource").value;
    let triggerCron = document.getElementById("trigger-cron").value;
    let triggerCode = document.getElementById("trigger-code").value;
    let triggerParameters = document.getElementById("trigger-parameters").getData();
    let triggerMessageType = triggerMessageTypeConvert(document.querySelector("input[name=trigger-message-type]:checked").id);
    let triggerMessageTemplate = templateInput.value;

    if (!validateTemplate()) {
        generateToast(
            "Invalid Message Template",
            "LiquidJS failed to parse the provided message template. Please see the error message below the inputted template.",
            "error"
        );
        return;
    }

    tfetch("POST", "notification/trigger", {
        body: {
            name: triggerName,
            description: triggerDescription,
            resource: triggerResource,
            cron: triggerCron,
            code: triggerCode,
            parameters: triggerParameters,
            message_type: triggerMessageType,
            message_template: triggerMessageTemplate,
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
}

ready(() => {
    liquidEngine = new liquidjs.Liquid();

    try {
        document.getElementById("trigger-create").addEventListener("click", createTrigger);
    } catch (error) {
        // Handle when template does not include trigger-create button as the page is loaded to update the trigger
    }

    try {
        document.getElementById("trigger-update").addEventListener("click", null);
    } catch (error) {
        // Handle when template does not include trigger-update button as the page is loaded to create a new trigger
    }

    templateInput.addEventListener("input", debounce(validateTemplate, 1000));
});

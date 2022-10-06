// ==UserScript==
// @name         Tornium Assists
// @namespace    http://torn.deek.sh
// @version      0.0.2
// @updateURL    https://torn.deek.sh/userscripts/tornium-assists.user.js
// @downloadURL  https://torn.deek.sh/userscripts/tornium-assists.user.js
// @author       tiksan [2383326]
// @match        https://www.torn.com/*
// @icon         https://torn.deek.sh/favicon.svg
// @grant        GM_xmlhttpRequest
// @require      https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js
// @connect      deek.sh
// @connect      localhost
// ==/UserScript==

const DEBUG = false;
const key = "";

if(DEBUG) {
    console.log("Script start");
}

$(document).ready(function() {
    if(DEBUG) {
        console.log("Document ready");
    }

    let button = document.createElement("button");
    button.classList.add("torn-btn");
    button.style.setProperty("margin-left", "1rem");

    $("div[class^='titleContainer__']").append(button);

    button.innerHTML = "Assist";
    button.onclick = function() {
        if(DEBUG) {
            console.log("Button pressed");
        }

        let url = new URL(document.URL);
        let urlParams = new URLSearchParams(url.search);

        if (DEBUG) {
            console.log(url);
            console.log(urlParams);
        }

        if(url.hostname !== 'www.torn.com' || (url.pathname !== '/loader.php' && url.pathname !== '/loader2.php')) {
            if(DEBUG) {
                console.log('Hostname or pathname not matching');
            }
    
            return;
        } else if(urlParams.get('sid') !== 'attack' && urlParams.get('sid') !== 'getInAttack') {
            if(DEBUG) {
                console.log('SID not matching');
            }

            return;
        }

        let data = {
            "target_tid": urlParams.get("user2ID")
        };

        sendData("https://torn.deek.sh/api/faction/assist", data)
    }
});

function sendData(endpoint, data) {
    GM_xmlhttpRequest({
        method: "POST",
        url: endpoint,
        data: JSON.stringify(data),
        responseType: "JSON",
        headers: {
            "Authorization": `Basic ${btoa(`${key}:`)}`
        },
        onload: function(response) {
            if(DEBUG) {
                console.log([
                    response.status,
                    response.statusText,
                    response.readyState,
                    response.responseHeaders,
                    response.responseText,
                    response.finalUrl
                ].join("\n"));
            }
        }
    });
}

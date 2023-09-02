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

var items = null;

function _writeItems() {
    $.each(items, function (itemID, itemName) {
        $(".item-selector").append(
            $("<option>", {
                value: itemID,
                text: itemName,
            })
        );
    });
}

let itemsRequest = (obj) => {
    var localItems = JSON.parse(localStorage.getItem("items"));

    if (localItems && Math.floor(Date.now() / 1000) - localItems.timestamp < 3600) {
        return new Promise((resolve, reject) => {
            items = localItems.items;
            _writeItems();
            resolve();
        });
    } else {
        return new Promise((resolve, reject) => {
            let xhttp = new XMLHttpRequest();

            xhttp.onload = function () {
                let response = xhttp.response;

                if ("code" in response) {
                    generateToast("Torn Items Not Located", response["message"]);
                    reject();
                    return;
                }

                items = response.items;
                _writeItems();
                localStorage.setItem(
                    "items",
                    JSON.stringify({
                        timestamp: Math.floor(Date.now() / 1000),
                        items: items,
                    })
                );
                resolve();
            };

            xhttp.responseType = "json";
            xhttp.open("GET", "/api/items");
            xhttp.setRequestHeader("Content-Type", "application/json");
            xhttp.send();
        });
    }
};

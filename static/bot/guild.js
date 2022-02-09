/* This file is part of Tornium.

Tornium is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Tornium is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Tornium.  If not, see <https://www.gnu.org/licenses/>. */

const guildid = document.currentScript.getAttribute('data-guildid');

$(document).ready(function(){
    $('[data-bs-toggle="tooltip"]').tooltip({
        container: '.list-group'
    });

    $('#stakeoutcategory').on('keypress', function(e) {
        if(e.which === 13) {
            const id = $('#stakeoutcategory').val();
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function() {
                window.location.reload();
            }

            xhttp.open('POST', `/bot/stakeouts/${guildid}/update?action=category&value=${id}`);
            xhttp.send();
        }
    });

    $('#assistchannel').on('keypress', function(e) {
        if(e.which === 13) {
            const id = $('#assistchannel').val();
            const xhttp = new XMLHttpRequest();

            xhttp.onload = function() {
                window.location.reload();
            }

            xhttp.open('POST', `/bot/assists/${guildid}/update?action=channel&value=${id}`);
            xhttp.send();
        }
    });
});

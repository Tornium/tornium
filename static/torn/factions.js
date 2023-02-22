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

$(document).ready(function() {
    var table = $('#factions-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": false,
        "ajax": {
            url: "/torn/factionsdata"
        },
        "scrollX": true
    });

    $('[data-bs-toggle="tooltip"]').tooltip({
        container: '.list-group'
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#factions-table tbody').on('click', 'tr', function() {
        if(table.row(this).data()[0] == 0) {
            return;
        }
        
        let xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));

            var membersTable = $('#member-table').DataTable({
                "processing": true,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            });

            xhttp = new XMLHttpRequest();
            xhttp.onload = function() {
                xhttp.response.forEach(function(member) {
                    if(member["discord_id"] == 0) {
                        membersTable.row.add([
                            member["username"],
                            member["level"],
                            `<span data-bs-toggle="tooltip" data-bs-placement="right" title="Last Action: ${member["last_action"]}">${member["status"]}</span>`,
                            `Unknown`
                        ]).draw();
                    } else {
                        membersTable.row.add([
                            member["username"],
                            member["level"],
                            `<span data-bs-toggle="tooltip" data-bs-placement="right" title="Last Action: ${member["last_action"]}">${member["status"]}</span>`,
                            `<a href="https://discordapp.com/users/${member["discord_id"]}" target="_blank" rel="noopener noreferer">${member["discord_id"]}</a>`
                        ]).draw();
                    }
                });

                modal.show();
            }
            xhttp.responseType = "json";
            xhttp.open('GET', '/torn/faction/members/' + factionID)
            xhttp.send();
        }
        const factionID = table.row(this).data()[0];

        xhttp.open('GET', '/torn/faction/' + factionID);
        xhttp.send();
    });
    
    const urlParams = new URLSearchParams(window.location.search);

    if(urlParams.get('tid') !== null && urlParams.get('tid') != 0) {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));

            var membersTable = $('#member-table').DataTable({
                "processing": true,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            });

            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + urlParams.get('tid'));
        xhttp.send();
    }

    $('#factionid-button').on('click', function() {
        if($('#userid-input').val() == 0) {
            return;
        }

        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));

            var membersTable = $('#member-table').DataTable({
                "processing": true,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            });

            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + $('#factionid-input').val());
        xhttp.send();
    });
});

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
    var table = $('#users-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/torn/usersdata"
        },
        "columns": [
            {data: "tid"},
            {data: "name"},
            {data: "level"},
            {data: "faction"},
            {data: {_: "last_action.display", sort: "last_action.timestamp"}},
            {data: {_: "last_refresh.display", sort: "last_refresh.timestamp"}}
        ]
    });

    var psTable = $('#users-ps-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/torn/userspsdata"
        },
        "columns": [
            {data: "tid"},
            {data: "name"},
            {data: {_: "useractivity.display", sort: "useractivity.sort"}},
            {data: "attackswon"},
            {data: "statenhancersused"},
            {data: "xanused"},
            {data: "lsdused"},
            {data: "networth"},
            {data: "energydrinkused"},
            {data: "refills"},
            {data: {_: "update.display", sort: "update.timestamp"}}
        ]
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#users-table tbody').on('click', 'tr', function() {
        if(table.row(this).data().tid == 0) {
            return;
        }

        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#user-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('user-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#user-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/user/' + table.row(this).data().tid);
        xhttp.send();
    });

    $("#users-ps-table tbody").on("click", "tr", function() {
        if(psTable.row(this).data().tid == 0) {
            return;
        }

        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#user-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('user-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#user-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/user/' + psTable.row(this).data().tid);
        xhttp.send();
    });

    const urlParams = new URLSearchParams(window.location.search);

    if(urlParams.get('tid') !== null && urlParams.get('tid') != 0) {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#user-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('user-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#user-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/user/' + urlParams.get('tid'));
        xhttp.send();
    }

    $('#userid-button').on('click', function() {
        if($('#userid-input').val() == 0) {
            return;
        }

        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#user-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('user-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#user-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/user/' + $('#userid-input').val());
        xhttp.send();
    });
});

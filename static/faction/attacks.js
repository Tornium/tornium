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

const key = document.currentScript.getAttribute('data-key');

$(document).ready(function() {
    $('#recent-attacks-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": false,
        "searching": false,
        "ajax": {
            url: "/faction/attacks/recent",
        },
        "columns": [
            {data: "attacker"},
            {data: "attacker_faction"},
            {data: "defender"},
            {data: "defender_faction"},
            {data: "respect"},
            {data: "result"},
            {data: "timestamp"}
        ],
        "scrollX": true
    });

    $.fn.dataTable.ext.pager.numbers_length = 5;
});

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

$(document).ready(function () {
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true,
    });

    $("#members-table").DataTable({
        paging: true,
        ordering: true,
        responsive: false,
        lengthMenu: [
            [10, 25, 50, -1],
            [10, 25, 50, "All"],
        ],
        displayLength: 25,
        order: [
            [2, "desc"],
            [1, "desc"],
        ],
        columnDefs: [{ orderable: false, targets: 0 }],
        scrollX: true,
    });

    $.fn.dataTable.ext.pager.numbers_length = 5;
});

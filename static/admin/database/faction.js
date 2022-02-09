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

$(document).ready(function() {
    var table = $('#faction-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/admin/database/factions"
        }
    });
    
    $.fn.dataTable.ext.pager.numbers_length = 5;
    
    $('#faction-table tbody').on('click', 'tr', function() {
        window.location.href = '/admin/database/faction/' + table.row(this).data()[0];
    });
});

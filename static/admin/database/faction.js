/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

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

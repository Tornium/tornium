/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    var table = $('#server-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/admin/database/servers"
        }
    });
    
    $.fn.dataTable.ext.pager.numbers_length = 5;
    
    $('#user-table tbody').on('click', 'tr', function() {
        window.location.href = '/admin/database/server/' + table.row(this).data()[0];
    });
});

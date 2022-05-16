/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    var table = $('#stats-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/astats/dbdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#stats-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#stats-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('stats-modal'));
                modal.dispose();
            }
            
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#stats-modal'));
            $('#user-table').DataTable({
                "paging": true,
                "ordering": true,
                "responsive": true,
                "autoWidth": false,
                "order": [[0, "desc"]]
            });
            modal.show();
        }
        xhttp.open('GET', '/astats/userdata?user=' + table.row(this).data()[0]);
        xhttp.send();
    })
});

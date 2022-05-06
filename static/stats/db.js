/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    var table = $('#stats-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/stats/dbdata",
            data: function(d) {
                d.minBS = $('#min-bs').val();
                d.maxBS = $('#max-bs').val();
            }
        },
        "order": [[2, "desc"], [1, "desc"]]
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
        xhttp.open('GET', '/stats/userdata?user=' + table.row(this).data()[0]);
        xhttp.send();
    });

    $('#min-bs').on('change', function() {
        table.ajax.reload();
    });

    $('#max-bs').on('change', function() {
        table.ajax.reload();
    });
});

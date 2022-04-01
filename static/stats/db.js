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
            url: "/stats/dbdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#stats-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#stats-modal').length) {
                var modal = new bootstrap.Modal.getInstance($('#stats-modal'));
                modal.dispose();
            }
            
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#stats-modal'));
            modal.show();
        }
        xhttp.open('GET', '/stats/userdata?user=' + table.row(this).data()[0]);
        xhttp.send();
    });
});

/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    var table = $('#users-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/torn/usersdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#users-table tbody').on('click', 'tr', function() {
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
        xhttp.open('GET', '/torn/user/' + table.row(this).data()[0]);
        xhttp.send();
    });

    const urlParams = new URLSearchParams(window.location.search);

    if(urlParams.get('tid') !== null) {
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
});

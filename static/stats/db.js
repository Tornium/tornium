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
    var modalOpen = false;

    $('#stats-table tbody').on('click', 'tr', function() {
        if(modalOpen) {
            $('#stats-modal').remove();
            modalOpen = false;
        }
        modalOpen = true;
        
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#stats-modal'));
            modal.show();
        }
        xhttp.open('GET', '/stats/userdata?user=' + table.row(this).data()[0]);
        xhttp.send();
    });
    
    $('.btn-close').on('click', function() {
        if(modalOpen) {
            modalOpen = false;
        }
    });
});

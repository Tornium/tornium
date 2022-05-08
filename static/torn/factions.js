/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    var table = $('#factions-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/torn/factionsdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#factions-table tbody').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + table.row(this).data()[0]);
        xhttp.send();
    });
    
    const urlParams = new URLSearchParams(window.location.search);

    if(urlParams.get('tid') !== null) {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + urlParams.get('tid'));
        xhttp.send();
    }

    $('#factionid-button').on('click', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));
            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + $('#factionid-input').val());
        xhttp.send();
    });
});

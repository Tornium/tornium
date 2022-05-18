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
        if(table.row(this).data()[0] == 0) {
            return;
        }
        
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));

            var membersTable = $('#member-table').DataTable({
                "processing": true,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            });

            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + table.row(this).data()[0]);
        xhttp.send();
    });
    
    const urlParams = new URLSearchParams(window.location.search);

    if(urlParams.get('tid') !== null && urlParams.get('tid') != 0) {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));

            var membersTable = $('#member-table').DataTable({
                "processing": true,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            });

            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + urlParams.get('tid'));
        xhttp.send();
    }

    $('#factionid-button').on('click', function() {
        if($('#userid-input').val() == 0) {
            return;
        }

        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            if($('#faction-modal').length) {
                var modal = bootstrap.Modal.getInstance(document.getElementById('faction-modal'));
                modal.dispose();
            }

            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#faction-modal'));

            var membersTable = $('#member-table').DataTable({
                "processing": true,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            });

            modal.show();
        }
        xhttp.open('GET', '/torn/faction/' + $('#factionid-input').val());
        xhttp.send();
    });
});

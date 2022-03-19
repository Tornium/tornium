/*
 Copyright (C) tiksan - All Rights Reserved
 Unauthorized copying of this file, via any medium is strictly prohibited
 Proprietary and confidential
 Written by tiksan <webmaster@deek.sh>
 */

$(document).ready(function() {
    $("#armory-users-table").DataTable({
        "processing": false,
        "serverSide": false,
        "ordering": false,
        "responsive": true,
    });

    var itemTable = $("#armory-items-table").DataTable({
        "processing": false,
        "serverSide": false,
        "ordering": true,
        "responsive": true,
        "ajax": {
            url: "/faction/armoryitemdata"
        }
    });

    $.fn.dataTable.ext.pager.numbers_length = 3;

    $('#armory-items-table').on('click', 'tr', function() {
        const xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#item-modal'));
            $("#item-table").DataTable({
                "processing": false,
                "serverSide": false,
                "ordering": true,
                "responsive": false
            })
            modal.show();
        }
        xhttp.open('GET', '/faction/armoryitem?tid=' + getTID(itemTable.row(this).data()[0]));
        xhttp.send();
    });
});

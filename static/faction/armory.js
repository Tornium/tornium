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
});

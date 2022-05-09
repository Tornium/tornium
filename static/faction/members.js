/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true
    });

    $('#members-table').DataTable({
        "paging": true,
        "ordering": true,
        "responsive": true,
        "lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
        "displayLength": 25,
        "order": [[2, "desc"], [1, "desc"]],
        "columnDefs": [{orderable: false, targets: 0}]
    })

    $.fn.dataTable.ext.pager.numbers_length = 5;
});
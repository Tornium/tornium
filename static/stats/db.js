/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip({
        html: true
    });

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
            let response = xhttp.response;

            if("code" in response) {
                generateToast("User Retrieval Failed", response["message"], "Error");
                return;
            }

            const user = response["user"];
            var modal = new bootstrap.Modal($("#stats-modal"));

            $("#stat-modal-label").text(`${user.name} [${user.tid}]`);
            $("#stat-modal-attack-link").attr("href", `https://www.torn.com/loader.php?sid=attack&user2ID=${user.tid}`);
            $("#stat-modal-profile-link").attr("href", `https://www.torn.com/profiles.php?XID=${user.tid}`);
            $("#stat-modal-level").text(user.level);
            $("#stat-modal-faction").text("NYI");
            $("#stat-modal-last-action").append($("<span>", {
                "data-bs-toggle": "tooltip",
                "data-bs-placement": "right",
                "title": tcttime(user.last_action),
                "text": reltime(user.last_action)
            }));
            $("#stat-modal-ff").text("NYI");
            $("#stat-modal-respect").text("NYI");
            $("#stat-modal-last-refresh").append($("<span>", {
                "data-bs-toggle": "tooltip",
                "data-bs-placement": "right",
                "title": tcttime(user.last_refresh),
                "text": reltime(user.last_refresh)
            }));

            $("#stat-modal-user-table-body").empty();

            $.each(response["stat_entries"], function(stat_id, stat) {
                $("#stat-modal-user-table-body").append($("<tr>", {
                    "data-statid": stat_id
                }));

                let statRow = $(`tr[data-statid="${stat_id}"]`);

                statRow.append($("<th>", {
                    "text": commas(stat.battlescore)
                }));
                statRow.append($("<th>", {
                    "class": "stat-timeadded"
                }));
                statRow.find(".stat-timeadded")[0].append($("<span>", {
                    "data-bs-toggle": "tooltip",
                    "data-bs-placement": "right",
                    "title": tcttime(stat.timeadded),
                    "text": reltime(stat.timeadded)
                }));

                if(stat.addedfactiontid === 0) {
                    statRow.append($("<th>", {
                        "text": "Unknown/No Faction"
                    }));
                } else if(stat.addedfaction == null) {
                    statRow.append($("<th>", {
                        "text": `Unknown Faction ID ${stat.addedfactiontid}`
                    }));
                } else {
                    statRow.append($("<th>", {
                        "text": `${stat.addedfaction.name} [${stat.addedfactiontid}]`
                    }));
                }
            });

            $('#stat-modal-user-table').DataTable({
                "paging": true,
                "ordering": true,
                "responsive": true,
                "autoWidth": false,
                "order": [[0, "desc"]]
            });
            modal.show();
        }

        xhttp.responseType = "json";
        xhttp.open("GET", `/api/stat/${table.row(this).data()[0]}`);
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send();
    });

    $('#min-bs').on('change', function() {
        table.ajax.reload();
    });

    $('#max-bs').on('change', function() {
        table.ajax.reload();
    });
});

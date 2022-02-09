/* This file is part of Tornium.

Tornium is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Tornium is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Tornium.  If not, see <https://www.gnu.org/licenses/>. */

const key = document.currentScript.getAttribute('data-key');

$(document).ready(function() {
    var table = $('#schedule-table').DataTable({
        "processing": true,
        "serverSide": true,
        "ordering": false,
        "responsive": true,
        "ajax": {
            url: "/faction/scheduledata"
        }
    });

    $('#schedule-table tbody').on('click', 'tr', function() {
        const id = table.row(this).data()[0];

        let xhttp = new XMLHttpRequest();
        xhttp.onload = function() {
            document.getElementById('modal').innerHTML = this.responseText;
            var modal = new bootstrap.Modal($('#schedule-modal'));
            modal.show();

            xhttp = new XMLHttpRequest();

            xhttp.onload = function() {
                var response = xhttp.response;

                var watchersTable = $('#possible-watchers-table').DataTable({
                    "processing": true,
                    "ordering": false,
                    "responsive": true,
                    "searching": false
                });

                response.forEach(function(user) {
                    watchersTable.row.add(user).draw();
                })

                $('#form-add-user').submit(function(e) {
                    e.preventDefault();

                    xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                        var response = xhttp.response;

                        if("code" in response) {
                            generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
                        } else {
                            watchersTable.clear().draw()
                            for(let user in response['activity']) {
                                watchersTable.row.add([
                                    user,
                                    response['activity'][user],
                                    response['weight'][user]
                                ]).draw()
                            }
                        }
                    };

                    xhttp.responseType = 'json';
                    xhttp.open('POST', '/api/faction/schedule/watcher');
                    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
                    xhttp.setRequestHeader("Content-Type", "application/json");
                    xhttp.send(JSON.stringify({
                        'uuid': id,
                        'tid': this.tid.value,
                        'weight': this.weight.value
                    }))
                });

                $('#form-add-activity').submit(function(e) {
                    e.preventDefault();

                    xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                        var response = xhttp.response;

                        if("code" in response) {
                            generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
                        } else {
                            watchersTable.clear().draw()
                            for(let user in response['activity']) {
                                watchersTable.row.add([
                                    user,
                                    response['activity'][user],
                                    response['weight'][user]
                                ]).draw()
                            }
                        }
                    }

                    xhttp.responseType = 'json';
                    xhttp.open('POST', '/api/faction/schedule/activity');
                    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
                    xhttp.setRequestHeader("Content-Type", "application/json");
                    xhttp.send(JSON.stringify({
                        'uuid': id,
                        'tid': this.tid.value,
                        'from': this.fromdatepicker.value - new Date().getTimezoneOffset() * 60,
                        'to': this.todatepicker.value - new Date().getTimezoneOffset() * 60
                    }))
                })

                $('#form-remove-user').submit(function(e) {
                    e.preventDefault();

                    xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                        var response = xhttp.response;

                        if("code" in response) {
                            generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
                        } else {
                            watchersTable.clear().draw()
                            for(let user in response['activity']) {
                                watchersTable.row.add([
                                    user,
                                    response['activity'][user],
                                    response['weight'][user]
                                ]).draw()
                            }
                        }
                    }

                    xhttp.responseType = 'json';
                    xhttp.open('DELETE', '/api/faction/schedule/watcher');
                    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
                    xhttp.setRequestHeader("Content-Type", "application/json");
                    xhttp.send(JSON.stringify({
                        'uuid': id,
                        'tid': this.tid.value
                    }))
                })

                $('#form-schedule-setup').submit(function(e) {
                    e.preventDefault();

                    xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                        var response = xhttp.response;

                        if("code" in response) {
                            generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
                        }
                    }

                    xhttp.responseType = 'json';
                    xhttp.open('POST', '/api/faction/schedule/setup');
                    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
                    xhttp.setRequestHeader("Content-Type", "application/json");
                    xhttp.send(JSON.stringify({
                        'uuid': id,
                        'from': this.fromts.value - new Date().getTimezoneOffset() * 60,
                        'to': this.tots.value - new Date().getTimezoneOffset() * 60
                    }))
                });

                $("#fromdatepicker").flatpickr({
                    enableTime: true,
                    dateFormat: "U",
                    altInput: true,
                    altFormat: "m/d H:i TCT",
                    minuteIncrement: 30
                });

                $("#fromts").flatpickr({
                    enableTime: true,
                    dateFormat: "U",
                    altInput: true,
                    altFormat: "m/d H:i TCT",
                    minuteIncrement: 30
                });

                $("#todatepicker").flatpickr({
                    enableTime: true,
                    dateFormat: "U",
                    altInput: true,
                    altFormat: "m/d H:i TCT",
                    minuteIncrement: 30
                });

                $("#tots").flatpickr({
                    enableTime: true,
                    dateFormat: "U",
                    altInput: true,
                    altFormat: "m/d H:i TCT",
                    minuteIncrement: 30
                });
            }
            xhttp.responseType = 'json';
            xhttp.open('GET', '/faction/schedule?uuid=' + id + '&watchers=True');
            xhttp.send();
        }
        xhttp.open('GET', '/faction/schedule?uuid=' + id);
        xhttp.send();
    });

    $('#create-schedule').click(function() {
        const xhttp = new XMLHttpRequest();
        var value = $("#requestamount").val();

        xhttp.onload = function() {
            var response = xhttp.response;

            if("code" in response) {
                generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
            } else {
                $('#schedule-table').DataTable().ajax.reload();
            }
        }

        xhttp.responseType = "json";
        xhttp.open("POST", "/api/faction/schedule");
        xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
        xhttp.setRequestHeader("Content-Type", "application/json");
        xhttp.send(JSON.stringify({
            'amount_requested': value
        }));
    });
});

function deleteSchedule() {
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        var response = xhttp.response;

        if("code" in response && response["code"] !== 0) {
            generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
        } else {
            $('#schedule-table').DataTable().ajax.reload();
        }
    }

    xhttp.responseType = "json";
    xhttp.open("DELETE", "/api/faction/schedule");
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send(JSON.stringify({
        'uuid': document.getElementById('schedule-modal').getAttribute('data-uuid')
    }));
}

function exportSchedule() {
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        var response = xhttp.response;

        if("code" in response && response["code"] !== 0) {
            generateToast("Request Failed", `The Tornium API server has responded with \"${response["message"]} to the submitted request.\"`);
        } else {
            var element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8, ' + encodeURIComponent(JSON.stringify(response)));
            element.setAttribute('download', `${document.getElementById('schedule-modal').getAttribute('data-uuid')}.json`);
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        }
    }

    xhttp.responseType = "json";
    xhttp.open("GET", `/api/faction/schedule/watcher/${document.getElementById('schedule-modal').getAttribute('data-uuid')}`);
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();
}

function runScheduler() {
    const xhttp = new XMLHttpRequest();
    xhttp.onload = function() {
        var response = xhttp.response;
    }

    xhttp.responseType = "json";
    xhttp.open("POST", `/api/faction/schedule/${document.getElementById('schedule-modal').getAttribute('data-uuid')}`);
    xhttp.setRequestHeader("Authorization", `Basic ${btoa(`${key}:`)}`);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send();
}

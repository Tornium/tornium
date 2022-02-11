/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh> */

google.charts.load('current', {packages: ['corechart']});

function createWatcherSchedule(data) {
    var container = document.getElementById('watcher-timeline');
    var timeline = new google.visualization.Timeline(container);
    var datatable = new google.visualization.DataTable();
    
    datatable.addColumn({'type': 'string', id: 'Type'});
    datatable.addColumn({'type': 'string', id: 'User ID'});
    datatable.addColumn({'type': 'date', id: 'Start'});
    datatable.addColumn({'type': 'date', id: 'End'});
    
    datatable.addRows(data);
    chart.draw(datatable);
}

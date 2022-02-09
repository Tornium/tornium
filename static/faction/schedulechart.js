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

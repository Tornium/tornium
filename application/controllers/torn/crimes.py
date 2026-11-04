# Copyright (C) 2021-2025 tiksan
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import abort, render_template
from peewee import DoesNotExist
from tornium_commons.models import OrganizedCrimeType
from tornium_commons.organized_crime_graph import to_graphviz

GRAPH_MIMETYPES = {"svg": "image/svg+xml", "png": "image/png", "dot": "text/vnd.graphviz"}


def crime_graphs():
    return render_template("torn/crime_graphs.html")


def render_crime_graph(oc_name, graph_extension):
    if graph_extension not in GRAPH_MIMETYPES:
        return abort(404)

    try:
        organized_crime_type: OrganizedCrimeType = (
            OrganizedCrimeType.select().where(OrganizedCrimeType.name == oc_name.replace("_", " ")).get()
        )
    except DoesNotExist:
        return abort(404)

    dot = to_graphviz(organized_crime_type)

    if graph_extension == "dot":
        return dot.source.encode(), 200, {"Content-Type": GRAPH_MIMETYPES[graph_extension]}
    else:
        return dot.pipe(format=graph_extension), 200, {"Content-Type": GRAPH_MIMETYPES[graph_extension]}

#!/usr/bin/env python3
#
#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import itertools
from datetime import datetime

from flask import Blueprint
from flask import render_template, url_for, redirect
from flask_wtf import FlaskForm

from app.datamgmt.case.case_db import get_case
from app.datamgmt.case.case_events_db import get_case_events_graph
from app.util import response_success, login_required, api_login_required

case_graph_blueprint = Blueprint('case_graph',
                                 __name__,
                                 template_folder='templates')


# CONTENT ------------------------------------------------
@case_graph_blueprint.route('/case/graph', methods=['GET'])
@login_required
def case_graph(caseid, url_redir):
    if url_redir:
        return redirect(url_for('case_graph.case_graph', cid=caseid, redirect=True))

    case = get_case(caseid)
    form = FlaskForm()

    return render_template("case_graph.html", case=case, form=form)


@case_graph_blueprint.route('/case/graph/getdata', methods=['GET'])
@api_login_required
def case_graph_get_data(caseid):
    events = get_case_events_graph(caseid)

    nodes = []
    edges = []
    dates = {
        "human": [],
        "machine": []
    }

    tmp = {}

    for event in events:
        ioc = "ioc_" if event.asset_compromised else ""
        atype = event.asset_type.lower()
        img = ""
        is_master_atype = False

        if 'computer' in atype:
            img = 'desktop.png'
            is_master_atype = True

        elif 'server' in atype:
            img = 'server.png'
            is_master_atype = True

        elif 'domain controller' in atype:
            img = 'windows_server.png'
            is_master_atype = True

        elif 'windows - dc' in atype:
            img = 'windows_server.png'
            is_master_atype = True

        elif 'account' in atype:
            img = 'user.png'

        elif 'vpn' in atype:
            img = 'vpn.png'
            is_master_atype = True

        elif 'firewall' in atype:
            img = 'firewall.png'
            is_master_atype = True

        elif 'router' in atype:
            img = 'router.png'
            is_master_atype = True

        elif 'WAF' in atype:
            img = 'firewall.png'
            is_master_atype = True

        elif 'switch' in atype:
            img = 'switch.png'
            is_master_atype = True

        elif 'phone' in atype:
            img = 'phone.png'
            is_master_atype = True

        elif 'windows' in atype:
            img = "windows_{}".format(img)

        else:
            img = 'question-mark.png'

        try:
            date = "{}-{}-{}".format(event.event_date.day, event.event_date.month, event.event_date.year)
        except:
            date = '15-05-2021'

        if date not in dates:
            dates['human'].append(date)
            dates['machine'].append(datetime.timestamp(event.event_date))

        if event.asset_ip:
            title = "{} -{}".format(event.asset_ip, event.asset_description)
        else:
            title = "{}".format(event.asset_description)

        new_node = {
            'id': event.asset_id,
            'label': event.asset_name,
            'image': '/static/assets/img/graph/' + ioc + img,
            'shape': 'image',
            'title': title,
            'value': 1
        }
        if not any(node['id'] == event.asset_id for node in nodes):
            nodes.append(new_node)

        ak = {
            'node_id': event.asset_id,
            'node_title': "{} -{}".format(event.event_date, event.event_title),
            'node_name': event.asset_name,
            'node_type': atype
        }
        if tmp.get(event.event_id):
            tmp[event.event_id]['list'].append(ak)
            if is_master_atype:
                tmp[event.event_id]['master_node'].append(event.asset_id)
        else:
            tmp[event.event_id] = {
                'master_node': [event.asset_id] if is_master_atype else [],
                'list': [ak],
                'color': event.event_color
            }

    node_dedup = {}
    for event_id in tmp:
        if tmp[event_id]['master_node']:
            for master_node in tmp[event_id]['master_node']:
                node_dedup[master_node] = []
                for subset in tmp[event_id]['list']:
                    if subset['node_id'] != master_node:
                        if subset['node_id'] in node_dedup and master_node in node_dedup.get(subset['node_id']):
                            continue

                        edge = {
                            'from': master_node,
                            'to': subset['node_id'],
                            'title': subset['node_title'],
                            'color': tmp[event_id]['color']
                        }
                        edges.append(edge)
                        node_dedup[master_node].append(subset['node_id'])
        else:
            for subset in itertools.combinations(tmp[event_id]['list'], 2):
                edge = {
                    'from': subset[0]['node_id'],
                    'to': subset[1]['node_id'],
                    'title': subset[0]['node_title'],
                    'color': tmp[event_id]['color']
                }
                edges.append(edge)

    resp = {
        'nodes': nodes,
        'edges': edges,
        'dates': dates
    }

    return response_success("", data=resp)

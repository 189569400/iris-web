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

# IMPORTS ------------------------------------------------
import marshmallow
from flask import Blueprint, url_for, render_template, request
from flask_wtf import FlaskForm
from werkzeug.utils import redirect

from app import db, app
from app.datamgmt.manage.manage_srv_settings_db import get_srv_settings, get_alembic_revision
from app.iris_engine.utils.tracker import track_activity
from app.schema.marshables import ServerSettingsSchema
from app.util import admin_required, api_admin_required, response_error, response_success

manage_srv_settings_blueprint = Blueprint(
    'manage_srv_settings_blueprint',
    __name__,
    template_folder='templates'
)


@manage_srv_settings_blueprint.route('/manage/settings', methods=['GET'])
@admin_required
def manage_settings(caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_srv_settings_blueprint.manage_settings', cid=caseid))

    form = FlaskForm()

    server_settings = get_srv_settings()

    versions = {
        "iris_current": app.config.get('IRIS_VERSION'),
        "api_min": app.config.get('API_MIN_VERSION'),
        "api_current": app.config.get('API_MAX_VERSION'),
        "interface_min": app.config.get('MODULES_INTERFACE_MIN_VERSION'),
        "interface_current": app.config.get('MODULES_INTERFACE_MAX_VERSION'),
        "db_revision": get_alembic_revision()
    }

    # Return default page of case management
    return render_template('manage_srv_settings.html', form=form, settings=server_settings, versions=versions)


@manage_srv_settings_blueprint.route('/manage/settings/updates', methods=['POST'])
@api_admin_required
def manage_update_settings(caseid):
    if not request.is_json:
        return response_error('Invalid request')

    srv_settings_schema = ServerSettingsSchema()
    server_settings = get_srv_settings()

    try:

        srv_settings_sc = srv_settings_schema.load(request.get_json(), instance=server_settings)
        db.session.commit()

        if srv_settings_sc:
            track_activity("Server settings updated", caseid=caseid)
            return response_success("Server settings updated", srv_settings_sc)

    except marshmallow.exceptions.ValidationError as e:
        return response_error(msg="Data error", data=e.messages, status=400)

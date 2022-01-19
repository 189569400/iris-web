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

# Python modules

# Flask modules

# App modules
import base64

from app import app, lm

# Blueprints
from app.blueprints.dashboard.dashboard_routes import dashboard_blueprint
from app.blueprints.login.login_routes import login_blueprint
from app.blueprints.manage.manage_customers_routes import manage_customers_blueprint
from app.blueprints.manage.manage_modules_routes import manage_modules_blueprint
from app.blueprints.profile.profile_routes import profile_blueprint
from app.blueprints.register.register_routes import register_blueprint
from app.blueprints.reports.reports_route import reports_blueprint
from app.blueprints.search.search_routes import search_blueprint
from app.blueprints.manage.manage_cases_routes import manage_cases_blueprint
from app.blueprints.manage.manage_assets_type_routes import manage_assets_blueprint
from app.blueprints.manage.manage_advanced_routes import manage_adv_blueprint
from app.blueprints.manage.manage_users import manage_users_blueprint
from app.blueprints.manage.manage_templates_routes import manage_templates_blueprint

from app.blueprints.tasks.tasks_routes import tasks_blueprint
from app.blueprints.context.context import ctx_blueprint
from app.blueprints.case.case_routes import case_blueprint
from app.blueprints.activities.activities_routes import activities_blueprint

from app.blueprints.api.api_routes import api_blueprint
from app.blueprints.manage.manage_analysis_status_routes import manage_anastatus_blueprint
from app.blueprints.manage.manage_ioc_types_routes import manage_ioc_type_blueprint
from app.blueprints.manage.manage_event_categories_routes import manage_event_cat_blueprint
from app.blueprints.manage.manage_objects_routes import manage_objects_blueprint
from app.blueprints.manage.manage_tlps_routes import manage_tlp_type_blueprint
from app.blueprints.manage.manage_task_status_routes import manage_task_status_blueprint

from app.models.models import User

from app.post_init import run_post_init

app.register_blueprint(dashboard_blueprint)
app.register_blueprint(login_blueprint)
app.register_blueprint(register_blueprint)
app.register_blueprint(profile_blueprint)
app.register_blueprint(search_blueprint)
app.register_blueprint(manage_cases_blueprint)
app.register_blueprint(manage_assets_blueprint)
app.register_blueprint(manage_adv_blueprint)
app.register_blueprint(manage_users_blueprint)
app.register_blueprint(manage_templates_blueprint)
app.register_blueprint(manage_modules_blueprint)
app.register_blueprint(manage_customers_blueprint)
app.register_blueprint(manage_anastatus_blueprint)
app.register_blueprint(manage_ioc_type_blueprint)
app.register_blueprint(manage_event_cat_blueprint)
app.register_blueprint(manage_objects_blueprint)
app.register_blueprint(manage_tlp_type_blueprint)
app.register_blueprint(manage_task_status_blueprint)

app.register_blueprint(tasks_blueprint)
app.register_blueprint(ctx_blueprint)
app.register_blueprint(case_blueprint)
app.register_blueprint(reports_blueprint)
app.register_blueprint(activities_blueprint)

app.register_blueprint(api_blueprint)

run_post_init(development=app.config["DEVELOPMENT"])


# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@lm.request_loader
def load_user_from_request(request):

    # first, try to login using the api_key url arg
    api_key = request.args.get('api_key')
    if api_key:
        user = User.query.filter(
            User.api_key == api_key,
            User.active == True
        ).first()
        if user:
            return user

    # next, try to login using Basic Auth
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Bearer ', '', 1)

        user = User.query.filter(
            User.api_key == api_key,
            User.active == True
        ).first()

        if user:
            return user

    # finally, return None if both methods did not login the user
    return None
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

from flask import Blueprint
from flask import render_template, request, url_for, redirect
from flask_login import login_user, current_user

from app import bc, db
from app.datamgmt.case.case_db import case_exists
from app.forms import LoginForm
from app.iris_engine.utils.tracker import track_activity
from app.models.cases import Cases
from app.models.models import User

login_blueprint = Blueprint(
    'login',
    __name__,
    template_folder='templates'
)


# CONTENT ------------------------------------------------
# Authenticate user
@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # cut the page for authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))

    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None
    c_exists = False

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str)

        # filter User out of database through username
        user = User.query.filter(
            User.user == username,
            User.active == True
        ).first()

        if user:
            if bc.check_password_hash(user.password, password):
                login_user(user)

                caseid = user.ctx_case

                if caseid is not None:
                    c_exists = case_exists(caseid=caseid)

                if caseid is None or not c_exists:
                    case = Cases.query.order_by(Cases.case_id).first()
                    user.ctx_case = case.case_id
                    user.ctx_human_case = case.name

                    db.session.commit()

                track_activity("user '{}' successfully logged-in".format(username), ctx_less=True)
                return redirect(url_for('index.index', cid=user.ctx_case))
            else:
                track_activity("wrong login password for user '{}'".format(username), ctx_less=True)
                msg = "Wrong password. Please try again."
        else:
            track_activity("someone tried to log with user '{}', which does not exist".format(username), ctx_less=True)
            msg = "Unknown user"

    return render_template('login.html', form=form, msg=msg)

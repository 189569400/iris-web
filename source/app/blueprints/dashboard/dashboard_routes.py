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
from datetime import datetime, timedelta

import marshmallow
from flask import Blueprint
from flask import render_template, request, url_for, redirect
from flask_login import logout_user, current_user
from sqlalchemy import distinct

from app import db
#from app.datamgmt.case.case_tasks_db import get_tasks_status
from app.datamgmt.dashboard.dashboard_db import list_global_tasks, update_gtask_status, list_user_tasks, \
    update_utask_status, get_tasks_status, get_global_task
from app.forms import CustomerForm, CaseGlobalTaskForm
from app.iris_engine.utils.tracker import track_activity
from app.models.cases import Cases
from app.models.models import Client, UserActivity
from app.models.models import FileContentHash, GlobalTasks, User, Ioc, CaseTasks
from app.schema.marshables import GlobalTasksSchema
from app.util import response_success, response_error, login_required, api_login_required

# CONTENT ------------------------------------------------
dashboard_blueprint = Blueprint(
    'index',
    __name__,
    template_folder='templates'
)


# Logout user
@dashboard_blueprint.route('/logout')
def logout():
    """
    Logout function. Erase its session and redirect to index i.e login
    :return: Page
    """
    track_activity("user '{}' has been logged-out".format(current_user.user), ctx_less=True)
    logout_user()

    return redirect(url_for('index.index'))


@dashboard_blueprint.route('/dashboard/case_charts', methods=['GET'])
@api_login_required
def get_cases_charts(caseid):
    """
    Get case charts
    :return: JSON
    """

    res = Cases.query.with_entities(
        Cases.open_date
    ).filter(
        Cases.open_date > (datetime.utcnow() - timedelta(days=365))
    ).order_by(
        Cases.open_date
    ).all()
    retr = [[], []]
    rk = {}
    for case in res:
        month = "{}/{}/{}".format(case.open_date.day, case.open_date.month, case.open_date.year)

        if month in rk:
            rk[month] += 1
        else:
            rk[month] = 1

        retr = [list(rk.keys()), list(rk.values())]

    return response_success("", retr)


@dashboard_blueprint.route('/')
def root():
    if not current_user.is_authenticated:
        return redirect(url_for('login.login'))
    else:
        return redirect(url_for('index.index'))


@dashboard_blueprint.route('/dashboard')
@login_required
def index(caseid, url_redir):
    """
    Index page. Load the dashboard data, create the add customer form
    :return: Page
    """
    if url_redir:
        return redirect(url_for('index.index', cid=caseid))

    msg = None
    now = datetime.utcnow()

    # Retrieve the dashboard data from multiple sources.
    # Quite fast as it is only counts.
    user_open_case = UserActivity.query.with_entities(
        distinct(Cases.case_id)
    ).filter(
        UserActivity.user_id == current_user.id,
        UserActivity.case_id == Cases.case_id,
        Cases.close_date == None
    ).count()

    data = {
        "user_open_count": user_open_case,
        "cases_open_count": db.session.query(Cases).filter(Cases.close_date == None).count(),
        "cases_count": db.session.query(Cases).count(),
    }

    # Create the customer form to be able to quickly add a customer
    form = CustomerForm(request.form)

    return render_template('index.html', data=data, form=form, msg=msg)


@dashboard_blueprint.route('/global/tasks/list', methods=['GET'])
@api_login_required
def get_gtasks(caseid):

    tasks_list = list_global_tasks()

    if tasks_list:
        output = [c._asdict() for c in tasks_list]
    else:
        output = []

    ret = {
        "tasks_status": get_tasks_status(),
        "tasks": output
    }

    return response_success("", data=ret)


@dashboard_blueprint.route('/global/tasks/<int:cur_id>', methods=['GET'])
@api_login_required
def view_gtask(cur_id, caseid):

    task = get_global_task(task_id=cur_id)
    if not task:
        return response_error(f'Global task ID {cur_id} not found')

    return response_success("", data=task._asdict())


@dashboard_blueprint.route('/user/tasks/list', methods=['GET'])
@api_login_required
def get_utasks(caseid):

    ct = list_user_tasks()

    if ct:
        output = [c._asdict() for c in ct]
    else:
        output = []

    ret = {
        "tasks_status": get_tasks_status(),
        "tasks": output
    }

    return response_success("", data=ret)


@dashboard_blueprint.route('/user/tasks/status/update', methods=['POST'])
@api_login_required
def utask_statusupdate(caseid):
    jsdata = request.get_json()
    if not jsdata:
        return response_error("Invalid request")

    task_id = jsdata.get('task_id')
    status = jsdata.get('task_status_id')
    case_id = jsdata.get('case_id')

    task = update_utask_status(task_id, status, case_id)

    if task:
        return response_success("Updated", data=task)

    return response_error("Invalid data")


@dashboard_blueprint.route('/global/tasks/status/update', methods=['POST'])
@api_login_required
def gtask_statusupdate(caseid):

    jsdata = request.get_json()
    if not jsdata:
        return response_error("Invalid request")

    task_id = jsdata.get('task_id')
    status = jsdata.get('task_status_id')

    success = update_gtask_status(task_id, status)

    if success:
        return response_success("Updated")

    return response_error("Invalid data")


@dashboard_blueprint.route('/global/tasks/add', methods=['GET', 'POST'])
@api_login_required
def add_gtask(caseid):
    task = GlobalTasks()

    form = CaseGlobalTaskForm()

    if form.is_submitted():

        try:

            gtask_schema = GlobalTasksSchema()
            gtask = gtask_schema.load(request.json)

        except marshmallow.exceptions.ValidationError as e:
            return response_error(msg="Data error", data=e.messages, status=400)

        gtask.task_userid_update = current_user.id
        gtask.task_open_date = datetime.utcnow()
        gtask.task_last_update = datetime.utcnow()
        gtask.task_last_update = datetime.utcnow()

        try:

            db.session.add(gtask)
            db.session.commit()

        except Exception as e:
            return response_error(msg="Data error", data=e.__str__(), status=400)

        track_activity("created new global task \'{}\'".format(gtask.task_title), caseid=caseid)

        return response_success('Saved !', data=gtask_schema.dump(gtask))

    else:
        form.task_assignee_id.choices = [(user.id, user.name) for user in User.query.filter(User.active == True).order_by(User.name).all()]
        form.task_status_id.choices = [(a.id, a.status_name) for a in get_tasks_status()]

        return render_template("modal_add_global_task.html", form=form, task=task, uid=current_user.id, user_name=None)


@dashboard_blueprint.route('/global/tasks/update/<int:cur_id>', methods=['GET', 'POST'])
@api_login_required
def edit_gtask(cur_id, caseid):

    if cur_id:
        form = CaseGlobalTaskForm()
        task = GlobalTasks.query.filter(GlobalTasks.id == cur_id).first()
        form.task_assignee_id.choices = [(user.id, user.name) for user in User.query.filter(User.active == True).order_by(User.name).all()]
        form.task_status_id.choices = [(a.id, a.status_name) for a in get_tasks_status()]

        if task:

            if form.is_submitted():

                try:
                    gtask_schema = GlobalTasksSchema()
                    gtask = gtask_schema.load(request.json, instance=task)
                    gtask.task_userid_update = current_user.id
                    gtask.task_last_update = datetime.utcnow()

                    db.session.commit()

                except marshmallow.exceptions.ValidationError as e:
                    return response_error(msg="Data error", data=e.messages, status=400)

                track_activity("updated global task {} (status {})".format(task.task_title, task.task_status_id), caseid=caseid)

                return response_success('Updated !', data=gtask_schema.dump(gtask))

            else:
                # Render the IOC
                form.task_title.render_kw = {'value': task.task_title}
                form.task_description.data = task.task_description
                user_name, = User.query.with_entities(User.name).filter(User.id == task.task_userid_update).first()

                return render_template("modal_add_global_task.html", form=form, task=task,
                                       uid=task.task_assignee_id, user_name=user_name)

    return response_error('Unknown task ID !')


@dashboard_blueprint.route('/global/tasks/delete/<int:cur_id>', methods=['GET'])
@api_login_required
def gtask_delete(cur_id, caseid):

    if not cur_id:
        return response_error("Missing parameter")

    data = GlobalTasks.query.filter(GlobalTasks.id == cur_id).first()
    if not data:
        return response_error("Invalid global task ID")

    GlobalTasks.query.filter(GlobalTasks.id == cur_id).delete()
    db.session.commit()

    track_activity("deleted global task ID {}".format(cur_id), caseid=caseid)

    return response_success("Task deleted")

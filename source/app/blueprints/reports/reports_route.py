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

# VARS ---------------------------------------------------

# CONTENT ------------------------------------------------
import tempfile
from flask import Blueprint
from flask import url_for, redirect, send_file

from app.iris_engine.module_handler.module_handler import call_modules_hook
from app.iris_engine.reporter.reporter import IrisMakeDocReport
from app.iris_engine.utils.tracker import track_activity
from app.models import CaseTemplateReport
from app.util import FileRemover, response_error, api_login_required

reports_blueprint = Blueprint('reports',
                              __name__,
                              template_folder='templates')

file_remover = FileRemover()


@reports_blueprint.route('/report/generate/activities/<report_id>', methods=['GET'])
@api_login_required
def download_case_activity(report_id, caseid):

    call_modules_hook('on_preload_activities_report_create', data=report_id, caseid=caseid)
    if report_id:
        report = CaseTemplateReport.query.filter(CaseTemplateReport.id == report_id).first()
        if report:
            tmp_dir = tempfile.mkdtemp()

            mreport = IrisMakeDocReport(tmp_dir, report_id, caseid)
            fpath = mreport.generate_doc_report(type="Activities")

            if fpath is None:
                track_activity("failed to generate a report")
                return response_error("Report error", "Failed to generate a report.")

            call_modules_hook('on_postload_activities_report_create', data=report_id, caseid=caseid)
            resp = send_file(fpath, as_attachment=True)
            file_remover.cleanup_once_done(resp, tmp_dir)

            track_activity("generated a report")

            return resp

    return redirect(url_for('index.index'))


@reports_blueprint.route("/report/generate/case/<report_id>")
@api_login_required
def _gen_report(report_id, caseid):

    call_modules_hook('on_preload_report_create', data=report_id, caseid=caseid)
    if report_id:
        report = CaseTemplateReport.query.filter(CaseTemplateReport.id == report_id).first()
        if report:
            tmp_dir = tempfile.mkdtemp()

            mreport = IrisMakeDocReport(tmp_dir, report_id, caseid)
            fpath = mreport.generate_doc_report(type="Investigation")

            if fpath is None:
                track_activity("failed to generate a report")
                return response_error("Report error", "Failed to generate a report.")

            call_modules_hook('on_postload_report_create', data=fpath, caseid=caseid)

            resp = send_file(fpath, as_attachment=True)
            file_remover.cleanup_once_done(resp, tmp_dir)

            track_activity("generated a report")

            return resp

    return redirect(url_for('index.index'))


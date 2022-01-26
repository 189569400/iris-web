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

import binascii

from sqlalchemy import and_

from app import db
from app.models.cases import Cases
from app.models.models import ReportType
from app.models.models import User, Client, CaseTemplateReport, Languages


def get_case_summary(caseid):
    case_summary = Cases.query.filter(
        Cases.case_id == caseid
    ).with_entities(
        Cases.name.label('case_name'),
        Cases.open_date.label('case_open'),
        User.name.label('user'),
        Client.name.label('customer')
    ).join(
        Cases.user, Cases.client
    ).first()

    return case_summary


def get_case(caseid):
    return Cases.query.filter(Cases.case_id == caseid).first()


def get_case_client_id(caseid):
    client_id = Cases.query.with_entities(
        Client.client_id
    ).filter(
        Cases.case_id == caseid
    ).join(Cases.client).first()

    return client_id


def case_get_desc(caseid):
    case_desc = Cases.query.with_entities(
        Cases.description
    ).filter(
        Cases.case_id == caseid
    ).first()

    return case_desc


def case_get_desc_crc(caseid):
    partial_case = case_get_desc(caseid)

    if partial_case:
        desc = partial_case.description
        if not desc:
            desc = ""
        desc_crc32 = binascii.crc32(desc.encode('utf-8'))
    else:
        desc = None
        desc_crc32 = None

    return desc_crc32, desc


def case_set_desc_crc(desc, caseid):
    lcase = get_case(caseid)

    if lcase:
        if not desc:
            desc = ""
        lcase.description = desc
        db.session.commit()
        return True

    return False


def get_case_report_template():
    reports = CaseTemplateReport.query.with_entities(
        CaseTemplateReport.id,
        CaseTemplateReport.name,
        Languages.name,
        CaseTemplateReport.description
    ).join(
        CaseTemplateReport.language,
        CaseTemplateReport.report_type
    ).filter(
        ReportType.name == "Investigation"
    ).all()

    return reports


def get_activities_report_template():
    reports = CaseTemplateReport.query.with_entities(
        CaseTemplateReport.id,
        CaseTemplateReport.name,
        Languages.name,
        CaseTemplateReport.description
    ).join(
        CaseTemplateReport.language,
        CaseTemplateReport.report_type
    ).filter(
        ReportType.name == "Activities"
    ).all()

    return reports


def case_name_exists(case_name, client_name):
    res = Cases.query.with_entities(
        Cases.name, Client.name
    ).filter(and_(
        Cases.name == case_name,
        Client.name == client_name
    )).join(
        Cases.client
    ).first()

    return True if res else False

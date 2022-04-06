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

import datetime

from sqlalchemy import desc

from app.models import User, Cases, Client, CaseReceivedFile, CasesEvent, CaseEventsAssets, CaseAssets, \
    AssetsType, IocLink, Ioc, IocAssetLink, AnalysisStatus, CaseTasks, Notes, EventCategory, IocType, TaskStatus


def export_case_json(case_id):
    """
    Fully export a case a JSON
    """
    export = {}
    case = export_caseinfo_json(case_id)

    if not case:
        export['errors'] = ["Invalid case number"]
        return export

    export['case'] = case
    export['evidences'] = export_case_evidences_json(case_id)
    export['timeline'] = export_case_tm_json(case_id)
    export['iocs'] = export_case_iocs_json(case_id)
    export['assets'] = export_case_assets_json(case_id)
    export['tasks'] = export_case_tasks_json(case_id)
    export['notes'] = export_case_notes_json(case_id)
    export['export_date'] = datetime.datetime.utcnow()

    return export


def export_caseinfo_json(case_id):

    case = Cases.query.filter(
        Cases.case_id == case_id
    ).with_entities(
        Cases.name,
        Cases.open_date,
        Cases.description,
        Cases.soc_id,
        User.name.label('opened_by'),
        Client.name.label('for_customer'),
        Cases.close_date,
        Cases.custom_attributes
    ).join(
        Cases.user, Cases.client
    ).all()

    if not case:
        return None

    return [row._asdict() for row in case][0]


def export_case_evidences_json(case_id):
    evidences = CaseReceivedFile.query.filter(
        CaseReceivedFile.case_id == case_id
    ).with_entities(
        CaseReceivedFile.filename,
        CaseReceivedFile.date_added,
        CaseReceivedFile.file_hash,
        User.name.label('added_by'),
        CaseReceivedFile.custom_attributes
    ).order_by(
        CaseReceivedFile.date_added
    ).join(
        CaseReceivedFile.user
    ).all()

    if evidences:
        return [row._asdict() for row in evidences]

    else:
        return []


def export_case_notes_json(case_id):
    res = Notes.query.with_entities(
        Notes.note_title,
        Notes.note_content,
        Notes.note_creationdate,
        Notes.note_lastupdate,
        Notes.custom_attributes
    ).filter(
        Notes.note_case_id == case_id
    ).all()

    if res:
        return [row._asdict() for row in res]

    return []


def export_case_tm_json(case_id):
    timeline = CasesEvent.query.with_entities(
        CasesEvent.event_id,
        CasesEvent.event_title,
        CasesEvent.event_date,
        CasesEvent.event_tz,
        CasesEvent.event_date_wtz,
        CasesEvent.event_content,
        CasesEvent.event_tags,
        CasesEvent.event_source,
        CasesEvent.event_raw,
        CasesEvent.custom_attributes,
        EventCategory.name.label('category'),
        User.name.label('last_edited_by')
    ).filter(
        CasesEvent.case_id == case_id
    ).order_by(
        CasesEvent.event_date
    ).join(
        CasesEvent.user
    ).outerjoin(
        CasesEvent.category
    ).all()

    tim = []
    for row in timeline:
        ras = row._asdict()
        ras['assets'] = None

        as_list = CaseEventsAssets.query.with_entities(
            CaseAssets.asset_id,
            CaseAssets.asset_name,
            AssetsType.asset_name.label('type')
        ).filter(
            CaseEventsAssets.event_id == row.event_id
        ).join(CaseEventsAssets.asset, CaseAssets.asset_type).all()

        alki = []
        for asset in as_list:
            alki.append("{} ({})".format(asset.asset_name, asset.type))

        ras['assets'] = alki

        tim.append(ras)

    return tim


def export_case_iocs_json(case_id):
    res = IocLink.query.with_entities(
        Ioc.ioc_value,
        IocType.type_name,
        Ioc.ioc_tags,
        Ioc.ioc_description,
        Ioc.custom_attributes
    ).filter(
        IocLink.case_id == case_id
    ).join(
        IocLink.ioc,
        Ioc.ioc_type
    ).order_by(
        IocType.type_name
    ).all()

    if res:
        return [row._asdict() for row in res]

    return []


def export_case_tasks_json(case_id):
    res = CaseTasks.query.with_entities(
        CaseTasks.task_title,
        TaskStatus.status_name.label('task_status'),
        CaseTasks.task_tags,
        CaseTasks.task_open_date,
        CaseTasks.task_close_date,
        CaseTasks.task_last_update,
        CaseTasks.task_description,
        CaseTasks.custom_attributes,
        User.name.label('assigned_to')
    ).filter(
        CaseTasks.task_case_id == case_id
    ).join(
        CaseTasks.user_assigned, CaseTasks.status
    ).all()

    if res:
        return [row._asdict() for row in res]

    return []


def export_case_assets_json(case_id):
    ret = []

    res = CaseAssets.query.with_entities(
        CaseAssets.asset_id,
        CaseAssets.asset_name,
        CaseAssets.asset_description,
        CaseAssets.asset_compromised.label('compromised'),
        AssetsType.asset_name.label("type"),
        AnalysisStatus.name.label('analysis_status'),
        CaseAssets.date_added,
        CaseAssets.asset_domain,
        CaseAssets.asset_ip,
        CaseAssets.asset_info,
        CaseAssets.asset_tags,
        CaseAssets.custom_attributes
    ).filter(
        CaseAssets.case_id == case_id
    ).join(
        CaseAssets.asset_type, CaseAssets.analysis_status
    ).order_by(desc(CaseAssets.asset_compromised)).all()

    for row in res:
        row = row._asdict()
        row['light_asset_description'] = row['asset_description']

        ial = IocAssetLink.query.with_entities(
            Ioc.ioc_value,
            IocType.type_name,
            Ioc.ioc_description
        ).filter(
            IocAssetLink.asset_id == row['asset_id']
        ).join(
            IocAssetLink.ioc,
            Ioc.ioc_type
        ).all()

        if ial:
            row['asset_ioc'] = [row._asdict() for row in ial]
        else:
            row['asset_ioc'] = []

        ret.append(row)

    return ret
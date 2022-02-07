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

from app import db
from app.common.models import Cases
from app.common.models import UserActivity, User
from sqlalchemy import desc, and_, distinct


class ActivitiesManager(object):
    @staticmethod
    def get_auto_activities(caseid):
        """
        DB function to fetch the automatically generated activities
        caseid: the case from which to get activities
        """
        auto_activities = UserActivity.query.with_entities(
            User.name.label("user_name"),
            UserActivity.activity_date,
            UserActivity.activity_desc,
            UserActivity.user_input
        ).join(
            UserActivity.user
        ).filter(
            and_(
                UserActivity.case_id == caseid,
                UserActivity.activity_desc.notlike('[Unbound]%'),
                UserActivity.activity_desc.notlike('Started a search for %'),
                UserActivity.activity_desc.notlike('Updated global task %'),
                UserActivity.activity_desc.notlike('Created new global task %'),
                UserActivity.activity_desc.notlike('Started a new case creation %'),
                UserActivity.user_input == False
            )
        ).order_by(
            UserActivity.activity_date
        ).all()

        auto_activities = [row._asdict() for row in auto_activities]

        return auto_activities

    @staticmethod
    def get_manual_activities(caseid):
        """
        DB function to fetch the manually generated activities
        caseid: the case from which to get activities
        """
        manual_activities = UserActivity.query.with_entities(
            User.name.label("user_name"),
            UserActivity.activity_date,
            UserActivity.activity_desc,
            UserActivity.user_input
        ).join(
            UserActivity.user
        ).filter(
            and_(
                UserActivity.case_id == caseid,
                UserActivity.user_input == True
            )
        ).order_by(
            UserActivity.activity_date
        ).all()

        manual_activities = [row._asdict() for row in manual_activities]

        return manual_activities

    @staticmethod
    def get_all_user_activities():
        user_activities = UserActivity.query.with_entities(
            Cases.name.label("case_name"),
            User.name.label("user_name"),
            UserActivity.user_id,
            UserActivity.case_id,
            UserActivity.activity_date,
            UserActivity.activity_desc,
            UserActivity.user_input,
            UserActivity.is_from_api
        ).join(
            UserActivity.case, UserActivity.user
        ).order_by(desc(UserActivity.activity_date)).limit(10000).all()

        user_activities += UserActivity.query.with_entities(
            UserActivity.case_id.label("case_name"),
            UserActivity.user_id.label("user_name"),
            UserActivity.activity_date,
            UserActivity.activity_desc,
            UserActivity.user_input,
            UserActivity.is_from_api
        ).filter(
            UserActivity.case_id == None
        ).order_by(desc(UserActivity.activity_date)).limit(10000).all()

        return user_activities

    @staticmethod
    def _get_user_activities(case_id):
        ua = UserActivity.query.with_entities(
            UserActivity.activity_date,
            User.name,
            UserActivity.activity_desc,
            UserActivity.is_from_api
        ).filter(
            UserActivity.case_id == case_id
        ).join(
            UserActivity.user
        ).order_by(
            desc(UserActivity.activity_date)
        )

        return ua

    @staticmethod
    def list_user_activities(case_id, limit=40):
        return ActivitiesManager._get_user_activities(case_id).limit(limit).all()

    @staticmethod
    def create_user_activity(user_id, case_id, activity_date, message, user_input=False, is_from_api=False):
        ua = UserActivity()

        try:
            ua.user_id = user_id
        except:
            pass

        try:
            ua.case_id = case_id
        except Exception as e:
            pass

        ua.activity_date = activity_date
        ua.activity_desc = message

        ua.user_input = user_input

        ua.is_from_api = is_from_api

        db.session.add(ua)
        db.session.commit()

        return ua

    @staticmethod
    def _user_open_case(user_id):
        user_open_case = UserActivity.query.with_entities(
            distinct(Cases.case_id)
        ).filter(
            UserActivity.user_id == user_id,
            UserActivity.case_id == Cases.case_id,
            Cases.close_date == None
        )

        return user_open_case

    @staticmethod
    def count_user_open_case(user_id):
        return ActivitiesManager._user_open_case(user_id).count()

    @staticmethod
    def list_user_open_case(user_id):
        return ActivitiesManager._user_open_case(user_id).all()

    @staticmethod
    def delete_user_activities(case_id):
        UserActivity.query.filter(UserActivity.case_id == case_id).delete()

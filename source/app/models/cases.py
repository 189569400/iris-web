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
from sqlalchemy import Column, Date, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from flask_login import current_user
from datetime import datetime

from app import db
from app.datamgmt.states import update_timeline_state, update_tasks_state, update_evidences_state, update_ioc_state, \
    update_assets_state, update_notes_state
from app.models.models import Client


class Cases(db.Model):
    __tablename__ = 'cases'

    case_id = Column(Integer, primary_key=True)
    soc_id = Column(String(256))
    client_id = Column(ForeignKey('client.client_id'), nullable=False)
    name = Column(String(256))
    description = Column(Text)
    open_date = Column(Date)
    close_date = Column(Date)
    user_id = Column(ForeignKey('user.id'))

    client = relationship('Client')
    user = relationship('User')

    def __init__(self,
                 name=None,
                 soc_id=None,
                 client_id=None,
                 description=None,
                 gen_report=False,
                 user=None
                 ):
        self.name = name,
        self.soc_id = soc_id,
        self.client_id = client_id,
        self.description = description,
        self.user_id = current_user.id if current_user else user.id
        self.author = current_user.user if current_user else user.user
        self.description = description
        self.open_date = datetime.utcnow()
        self.gen_report = gen_report

    def save(self):
        """
        Save the current case in database
        :return:
        """
        # Inject self into db
        db.session.add(self)

        # Commit the changes
        db.session.commit()

        # Rename case with the ID
        self.name = "#{id} - {name}".format(id=self.case_id, name=self.name)

        # Create the states
        update_timeline_state(caseid=self.case_id, userid=self.user_id)
        update_tasks_state(caseid=self.case_id, userid=self.user_id)
        update_evidences_state(caseid=self.case_id, userid=self.user_id)
        update_ioc_state(caseid=self.case_id, userid=self.user_id)
        update_assets_state(caseid=self.case_id, userid=self.user_id)
        update_notes_state(caseid=self.case_id, userid=self.user_id)

        db.session.commit()

        return self

    def validate_on_build(self):
        """
        Execute an autocheck of the case metadata and validate it
        :return: True if valid else false; Tuple with errors
        """
        # TODO : Check if case name already exists

        res = Client.query\
            .with_entities(Client.client_id)\
            .filter(Client.client_id == self.client_id)\
            .first()

        self.client_id = res[0]

        return True, []


class CasesEvent(db.Model):
    __tablename__ = "cases_events"

    event_id = Column(Integer, primary_key=True)
    case_id = Column(ForeignKey('cases.case_id'))
    event_title = Column(Text)
    event_source = Column(Text)
    event_content = Column(Text)
    event_raw = Column(Text)
    event_date = Column(DateTime)
    event_added = Column(DateTime)
    event_in_graph = Column(Boolean)
    event_in_summary = Column(Boolean)
    user_id = Column(ForeignKey('user.id'))
    event_color = Column(Text)
    event_tags = Column(Text)
    event_tz = Column(Text)
    event_date_wtz = Column(DateTime)

    case = relationship('Cases')
    user = relationship('User')
    category = relationship('EventCategory', secondary="case_events_category",
                            primaryjoin="CasesEvent.event_id==CaseEventCategory.event_id",
                            secondaryjoin="CaseEventCategory.category_id==EventCategory.id",
                            viewonly=True)

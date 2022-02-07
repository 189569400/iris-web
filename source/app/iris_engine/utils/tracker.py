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
from datetime import datetime
from flask import request

from flask_login import current_user

from app import app

import logging as log


# CONTENT ------------------------------------------------
def track_activity(message, caseid=None, ctx_less=False, user_input=False):
    """
    Register a user activity in DB.
    :param message: Message to save as activity
    :return: Nothing
    """

    if caseid is None:
        caseid = current_user.ctx_case

    activity_desc = message.capitalize() if not ctx_less else "[Unbound] {}".format(message.capitalize())
    is_from_api = (request.cookies.get('session') is None if request else False)
    ua = app.activities_manager.create_user_activity(current_user.id, caseid, datetime.utcnow(), activity_desc,
                                                     user_input=user_input, is_from_api=is_from_api)

    log.info(activity_desc)

    return ua

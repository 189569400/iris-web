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
from unittest import TestCase
from unittest.mock import patch

from app import app
from app.util import response_success
from tests.test_helper import TestHelper

app.testing = True


class TestActivitiesRoutes(TestCase):
    def setUp(self) -> None:
        self._test_helper = TestHelper()

    def test_activities_index(self):
        self._test_helper.verify_path_with_cid(
            'activities.activities_index',
            '1'
        )

    def test_activities_index_should_redirect_to_cid_1_if_no_cid_is_provided(self):
        self._test_helper.verify_path_without_cid_redirects_correctly(
            'activities.activities_index',
            'You should be redirected automatically to target URL: <a href="/activities?cid=1">/activities?cid=1</a>'
        )

    def test_list_activities_verify_path(self):
        self._test_helper.verify_path_with_cid(
            'activities.list_activities',
            '1'
        )

    def test_list_activities(self):
        caseid = 1

        user_activities = [{'case_name': '#1 - Initial Demo', 'user_name': 'tester', 'user_id': 3, 'case_id': 1,
                            'activity_date': datetime.datetime(2022, 2, 7, 17, 38, 1, 375155),
                            'activity_desc': '[Unbound] Case 2 deleted successfully', 'user_input': False,
                            'is_from_api': False},
                           {'case_name': '#1 - Initial Demo', 'user_name': 'tester', 'user_id': 3, 'case_id': 1,
                            'activity_date': datetime.datetime(2022, 2, 8, 10, 26, 7, 836874),
                            'activity_desc': "[Unbound] User 'tester' successfully logged-in",
                            'user_input': False, 'is_from_api': False},
                           {'case_name': '#1 - Initial Demo', 'user_name': 'tester', 'user_id': 3, 'case_id': 1,
                            'activity_date': datetime.datetime(2022, 2, 7, 17, 43, 48, 508358),
                            'activity_desc': "Mais oui c'est clair", 'user_input': True, 'is_from_api': False}
                           ]

        user_activities_post_dict = [{'case_name': '#1 - Initial Demo', 'user_name': 'tester', 'user_id': 3,
                                      'case_id': 1, 'activity_date': datetime.datetime(2022, 2, 8, 10, 26, 7, 836874),
                                      'activity_desc': "[Unbound] User 'tester' successfully logged-in",
                                      'user_input': False, 'is_from_api': False},
                                     {'case_name': '#1 - Initial Demo', 'user_name': 'tester', 'user_id': 3,
                                      'case_id': 1, 'activity_date': datetime.datetime(2022, 2, 7, 17, 43, 48, 508358),
                                      'activity_desc': "Mais oui c'est clair", 'user_input': True,
                                      'is_from_api': False},
                                     {'case_name': '#1 - Initial Demo', 'user_name': 'tester', 'user_id': 3,
                                      'case_id': 1, 'activity_date': datetime.datetime(2022, 2, 7, 17, 38, 1, 375155),
                                      'activity_desc': '[Unbound] Case 2 deleted successfully', 'user_input': False,
                                      'is_from_api': False}]

        expected_return = response_success("", user_activities_post_dict)

        with patch.object(app.activities_manager, 'get_all_user_activities') as get_all_user_activities:
            get_all_user_activities.return_value = user_activities
            app.activities_manager.get_all_user_activities(caseid)

            self._test_helper.verify_response_with_cid(
                'activities.list_activities',
                '1',
                expected_return.data
            )

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


from unittest import TestCase

from app import app
from tests.test_helper import TestHelper

app.testing = True


class TestDashboardRoutes(TestCase):
    def setUp(self) -> None:
        self._test_helper = TestHelper()

    def test_logout(self):
        self.fail()

    def test_get_cases_charts(self):
        self.fail()

    def test_root(self):
        self.fail()

    def test_index(self):
        self.fail()

    def test_get_gtasks(self):
        self.fail()

    def test_view_gtask(self):
        self.fail()

    def test_get_utasks(self):
        self.fail()

    def test_utask_statusupdate(self):
        self.fail()

    def test_add_gtask(self):
        self.fail()

    def test_edit_gtask(self):
        self.fail()

    def test_gtask_delete(self):
        self.fail()

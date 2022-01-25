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


class TestCaseAssetsRoutes(TestCase):
    def setUp(self) -> None:
        self._test_helper = TestHelper()

    def test_case_assets(self):
        self.fail()

    def test_case_list_assets(self):
        self.fail()

    def test_case_assets_state(self):
        self.fail()

    def test_autoload_asset(self):
        self.fail()

    def test_add_asset_modal(self):
        self.fail()

    def test_add_asset(self):
        self.fail()

    def test_case_upload_asset(self):
        self.fail()

    def test_asset_view(self):
        self.fail()

    def test_asset_view_modal(self):
        self.fail()

    def test_asset_update(self):
        self.fail()

    def test_asset_delete(self):
        self.fail()

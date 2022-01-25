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


class TestCaseNotesRoutes(TestCase):
    def setUp(self) -> None:
        self._test_helper = TestHelper()

    def test_case_notes(self):
        self.fail()

    def test_case_note_detail(self):
        self.fail()

    def test_case_note_detail_modal(self):
        self.fail()

    def test_case_note_delete(self):
        self.fail()

    def test_case_note_save(self):
        self.fail()

    def test_case_note_add(self):
        self.fail()

    def test_case_load_notes_groups(self):
        self.fail()

    def test_case_notes_state(self):
        self.fail()

    def test_case_search_notes(self):
        self.fail()

    def test_case_add_notes_groups(self):
        self.fail()

    def test_case_delete_notes_groups(self):
        self.fail()

    def test_case_get_notes_group(self):
        self.fail()

    def test_case_edit_notes_groups(self):
        self.fail()

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


class TestManageModulesRoutes(TestCase):
    def setUp(self) -> None:
        self._test_helper = TestHelper()

    def test_case_get_manage_modules_index_should_redirect_to_cid_1_if_no_cid_is_provided(self):
        self._test_helper.verify_path_without_cid_redirects_correctly(
            'manage_module.manage_modules_index',
            'You should be redirected automatically to target URL: <a href="/manage/modules?cid=1">/manage/modules?cid=1</a>'
        )

    def test_site_map(self):
        self.fail()

    def test_manage_modules(self):
        self.fail()

    def test_manage_modules_list(self):
        self.fail()

    def test_add_module(self):
        self.fail()

    def test_update_module_param(self):
        self.fail()

    def test_view_module(self):
        self.fail()

    def test_enable_module(self):
        self.fail()

    def test_disable_module(self):
        self.fail()

    def test_view_delete_module(self):
        self.fail()
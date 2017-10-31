# -*- coding: utf-8 -*-
#
# Copyright © 2017  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#

'''
Tests for the Flask-RESTful based v2 API
'''
from __future__ import unicode_literals

import json

from anitya.lib import model
from .base import (DatabaseTestCase, create_project)


# Py3 compatibility: UTF-8 decoding and JSON decoding may be separate steps
def _read_json(output):
    return json.loads(output.get_data(as_text=True))


class ProjectsResourceGetTests(DatabaseTestCase):

    def setUp(self):
        super(ProjectsResourceGetTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = model.Session()
        self.user = model.User(email='user@example.com', username='user')
        self.api_token = model.ApiToken(user=self.user)
        session.add_all([self.user, self.api_token])
        session.commit()

    def test_no_projects(self):
        """Assert querying projects works, even if there are no projects."""
        output = self.app.get('/api/v2/projects/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

    def test_authenticated(self):
        """Assert the API works when authenticated."""
        output = self.app.get(
            '/api/v2/projects/', headers={'Authorization': 'Token ' + self.api_token.token})
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 25, 'total_items': 0, 'items': []})

    def test_list_projects(self):
        """Assert projects are returned when they exist."""
        create_project(self.session)

        output = self.app.get('/api/v2/projects/')
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 1,
            'items_per_page': 25,
            'total_items': 3,
            'items': [
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": []
                },
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "http://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://www.geany.org/Download/Releases",
                    "versions": []
                },
                {
                    "id": 2,
                    "backend": "custom",
                    "homepage": "http://subsurface.hohndel.org/",
                    "name": "subsurface",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://subsurface.hohndel.org/downloads/",
                    "versions": []
                }
            ]
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page(self):
        """Assert pagination works and page size is adjustable."""
        api_endpoint = '/api/v2/projects/?items_per_page=1'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 1, 'items_per_page': 1, 'total_items': 0, 'items': []})

        create_project(self.session)

        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 1,
            'items_per_page': 1,
            'total_items': 3,
            'items': [
                {
                    "id": 3,
                    "backend": "custom",
                    "homepage": "https://fedorahosted.org/r2spec/",
                    "name": "R2spec",
                    "regex": None,
                    "version": None,
                    "version_url": None,
                    "versions": []
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page_with_page(self):
        """Assert retrieving other pages works."""
        api_endpoint = '/api/v2/projects/?items_per_page=1&page=2'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        self.assertEqual(data, {'page': 2, 'items_per_page': 1, 'total_items': 0, 'items': []})

        create_project(self.session)

        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 200)
        data = _read_json(output)

        for item in data['items']:
            del item['created_on']
            del item['updated_on']

        exp = {
            'page': 2,
            'items_per_page': 1,
            'total_items': 3,
            'items': [
                {
                    "id": 1,
                    "backend": "custom",
                    "homepage": "http://www.geany.org/",
                    "name": "geany",
                    "regex": "DEFAULT",
                    "version": None,
                    "version_url": "http://www.geany.org/Download/Releases",
                    "versions": []
                },
            ]
        }

        self.assertEqual(data, exp)

    def test_list_projects_items_per_page_too_big(self):
        """Assert unreasonably large items per page results in an error."""
        api_endpoint = '/api/v2/projects/?items_per_page=500'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'items_per_page': u'Value must be less than or equal to 250.'}})

    def test_list_projects_items_per_page_negative(self):
        """Assert a negative value for items_per_page results in an error."""
        api_endpoint = '/api/v2/projects/?items_per_page=-25'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'items_per_page': u'Value must be greater than or equal to 1.'}})

    def test_list_projects_items_per_page_non_integer(self):
        """Assert a non-integer for items_per_page results in an error."""
        api_endpoint = '/api/v2/projects/?items_per_page=twenty'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data,
            {u'message': {u'items_per_page': u"invalid literal for int() with base 10: 'twenty'"}}
        )

    def test_list_projects_page_negative(self):
        """Assert a negative value for a page results in an error."""
        api_endpoint = '/api/v2/projects/?page=-25'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'page': u'Value must be greater than or equal to 1.'}})

    def test_list_projects_page_non_integer(self):
        """Assert a non-integer value for a page results in an error."""
        api_endpoint = '/api/v2/projects/?page=twenty'
        output = self.app.get(api_endpoint)
        self.assertEqual(output.status_code, 400)
        data = _read_json(output)

        self.assertEqual(
            data, {u'message': {u'page': u"invalid literal for int() with base 10: 'twenty'"}})


class ProjectsResourcePostTests(DatabaseTestCase):

    def setUp(self):
        super(ProjectsResourcePostTests, self).setUp()
        self.app = self.flask_app.test_client()
        session = model.Session()
        self.user = model.User(email='user@example.com', username='user')
        self.api_token = model.ApiToken(user=self.user)
        session.add_all([self.user, self.api_token])
        session.commit()

        self.auth = {'Authorization': 'Token ' + self.api_token.token}

    def test_unauthenticated(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post('/api/v2/projects/')

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_token(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post('/api/v2/projects/', headers={'Authorization': 'Token eh'})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_auth_type(self):
        """Assert unauthenticated requests result in a HTTP 401 response."""
        self.maxDiff = None
        error_details = {
            'error': 'authentication_required',
            'error_description': 'Authentication is required to access this API.',
        }

        output = self.app.post(
            '/api/v2/projects/', headers={'Authorization': 'Basic ' + self.api_token.token})

        self.assertEqual(output.status_code, 401)
        self.assertEqual(error_details, _read_json(output))
        self.assertEqual('Token', output.headers['WWW-Authenticate'])

    def test_invalid_request(self):
        """Assert invalid requests result in a helpful HTTP 400."""
        output = self.app.post('/api/v2/projects/', headers=self.auth)

        self.assertEqual(output.status_code, 400)
        # Error details should report the missing required fields
        data = _read_json(output)
        error_details = data["message"]
        self.assertIn("backend", error_details)
        self.assertIn("homepage", error_details)
        self.assertIn("name", error_details)

    def test_conflicting_request(self):
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        output = self.app.post('/api/v2/projects/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 201)
        output = self.app.post('/api/v2/projects/', headers=self.auth, data=request_data)
        self.assertEqual(output.status_code, 409)
        # Error details should report conflicting fields.
        data = _read_json(output)
        self.assertIn("requested_project", data)
        self.assertEqual("PyPI", data["requested_project"]["backend"])
        self.assertEqual("http://python-requests.org", data["requested_project"]["homepage"])
        self.assertEqual("requests", data["requested_project"]["name"])

    def test_valid_request(self):
        request_data = {
            "backend": "PyPI",
            "homepage": "http://python-requests.org",
            "name": "requests",
        }

        output = self.app.post('/api/v2/projects/', headers=self.auth, data=request_data)

        data = _read_json(output)
        self.assertEqual(output.status_code, 201)
        self.assertIn("backend", data)
        self.assertIn("homepage", data)
        self.assertIn("name", data)
        self.assertEqual("PyPI", data["backend"])
        self.assertEqual("http://python-requests.org", data["homepage"])
        self.assertEqual("requests", data["name"])
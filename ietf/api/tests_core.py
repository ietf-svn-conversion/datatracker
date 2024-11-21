# Copyright The IETF Trust 2024, All Rights Reserved
"""Core API tests"""
from unittest.mock import patch, call

from django.urls import reverse as urlreverse
from rest_framework.test import APIClient

from ietf.person.factories import PersonFactory, EmailFactory
from ietf.utils.test_utils import TestCase


class CoreApiTestCase(TestCase):
    client_class = APIClient


class PersonTests(CoreApiTestCase):
    def test_person_detail(self):
        person = PersonFactory()
        other_person = PersonFactory()
        url = urlreverse("ietf.api.core_api.person-detail", kwargs={"pk": person.pk})
        r = self.client.get(url, format="json")
        self.assertEqual(r.status_code, 403, "Must be logged in")
        self.client.login(
            username=other_person.user.username,
            password=other_person.user.username + "+password",
        )
        r = self.client.get(url, format="json")
        self.assertEqual(r.status_code, 403, "Can only retrieve self")
        self.client.login(
            username=person.user.username, password=person.user.username + "+password"
        )
        r = self.client.get(url, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "id": person.pk,
                "name": person.name,
                "emails": [
                    {
                        "person": person.pk,
                        "address": email.address,
                        "primary": email.primary,
                        "active": email.active,
                        "origin": email.origin,
                    }
                    for email in person.email_set.all()
                ],
            },
        )

    @patch("ietf.person.api.send_new_email_confirmation_request")
    def test_add_email(self, send_confirmation_mock):
        email = EmailFactory(address="old@example.org")
        person = email.person
        other_person = PersonFactory()
        url = urlreverse("ietf.api.core_api.person-email", kwargs={"pk": person.pk})
        post_data = {"address": "new@example.org"}

        r = self.client.post(url, data=post_data, format="json")
        self.assertEqual(r.status_code, 403, "Must be logged in")
        self.assertFalse(send_confirmation_mock.called)

        self.client.login(
            username=other_person.user.username,
            password=other_person.user.username + "+password",
        )
        r = self.client.post(url, data=post_data, format="json")
        self.assertEqual(r.status_code, 403, "Can only retrieve self")
        self.assertFalse(send_confirmation_mock.called)

        self.client.login(
            username=person.user.username, password=person.user.username + "+password"
        )
        r = self.client.post(url, data=post_data, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, {"address": "new@example.org"})
        self.assertTrue(send_confirmation_mock.called)
        self.assertEqual(
            send_confirmation_mock.call_args, call(person, "new@example.org")
        )


class EmailTests(CoreApiTestCase):
    def test_email_update(self):
        email = EmailFactory(
            address="original@example.org", primary=False, active=True, origin="factory"
        )
        person = email.person
        other_person = PersonFactory()
        url = urlreverse(
            "ietf.api.core_api.email-detail", kwargs={"pk": "original@example.org"}
        )
        bad_url = urlreverse(
            "ietf.api.core_api.email-detail",
            kwargs={"pk": "not-original@example.org"},
        )

        r = self.client.put(
            bad_url, data={"primary": True, "active": False}, format="json"
        )
        self.assertEqual(r.status_code, 403, "Must be logged in preferred to 404")
        r = self.client.put(url, data={"primary": True, "active": False}, format="json")
        self.assertEqual(r.status_code, 403, "Must be logged in")

        self.client.login(
            username=other_person.user.username,
            password=other_person.user.username + "+password",
        )
        r = self.client.put(
            bad_url, data={"primary": True, "active": False}, format="json"
        )
        self.assertEqual(r.status_code, 404, "No such address")
        r = self.client.put(url, data={"primary": True, "active": False}, format="json")
        self.assertEqual(r.status_code, 403, "Can only access own addresses")

        self.client.login(
            username=person.user.username, password=person.user.username + "+password"
        )
        r = self.client.put(url, data={"primary": True, "active": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "person": person.pk,
                "address": "original@example.org",
                "primary": True,
                "active": False,
                "origin": "factory",
            },
        )
        email.refresh_from_db()
        self.assertEqual(email.person, person)
        self.assertEqual(email.address, "original@example.org")
        self.assertTrue(email.primary)
        self.assertFalse(email.active)
        self.assertEqual(email.origin, "factory")

        # address / origin should be immutable
        r = self.client.put(
            url,
            data={
                "address": "modified@example.org",
                "primary": True,
                "active": False,
                "origin": "hacker",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data,
            {
                "person": person.pk,
                "address": "original@example.org",
                "primary": True,
                "active": False,
                "origin": "factory",
            },
        )
        email.refresh_from_db()
        self.assertEqual(email.person, person)
        self.assertEqual(email.address, "original@example.org")
        self.assertTrue(email.primary)
        self.assertFalse(email.active)
        self.assertEqual(email.origin, "factory")

    def test_email_partial_update(self):
        self.fail("not implemented")

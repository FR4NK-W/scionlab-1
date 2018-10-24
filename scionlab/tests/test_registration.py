# Copyright 2018 ETH Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from django_registration.backends.activation import urls

from scionlab.models import User
from scionlab.settings.common import BASE_DIR

_TESTUSER_EMAIL = 'scion4@example.com'
_TESTUSER_PWD = 'scionR0CK5'


class ActivationRequiredTest(TestCase):
    def test_account_not_activated(self):
        """
        Check that an account which has not been activated cannot login
        """

        login_url = reverse('login')

        response = self.client.get(login_url, follow=True)

        registration_url = reverse('registration_form')
        response = self.client.get(
            registration_url,
            follow=True
        )

        # Post registration:
        response = self.client.post(
            registration_url,
            {'email': _TESTUSER_EMAIL, 'password1': _TESTUSER_PWD, 'password2': _TESTUSER_PWD, 'username': _TESTUSER_EMAIL},
            follow=True
        )

        # Check the correct activation email is created
        self.assertEqual(len(mail.outbox), 1)
        activation_mail = mail.outbox[0]
        self.assertEqual(activation_mail.recipients(), [_TESTUSER_EMAIL])
        with open(os.path.join(BASE_DIR, 'scionlab', 'templates', 'django_registration', 'activation_email_subject.txt')) as f:
            activation_subject = f.read()
        self.assertEqual(activation_mail.subject, activation_subject)

        # Attempt log in:
        response = self.client.post(
            login_url,
            {'username': _TESTUSER_EMAIL, 'password': _TESTUSER_PWD},
            follow=True
        )

        # We should still be on the login page
        self.assertEqual(len(response.redirect_chain), 0)

        # Now we activate the account by using the link sent by email
        activation_mail_message = str(activation_mail.message().get_payload())
        links = re.findall('http://testserver(/\S*)', activation_mail_message, re.MULTILINE)

        activation_link = ''
        dummy_activation_key = 'XXX'
        for link in links:
            if reverse('django_registration_activate', kwargs={'activation_key': dummy_activation_key}).split(dummy_activation_key)[0] in link:
                activation_link = link
                break

        self.assertNotEqual(activation_link, '')

        # Use the activation link
        response = self.client.get(
            activation_link,
            follow=True
        )

        self.assertTemplateUsed(
            response,
            'django_registration/activation_complete.html',
            "Expected account activation complete template."
        )

        # Attempt log in:
        response = self.client.post(
            login_url,
            {'username': _TESTUSER_EMAIL, 'password': _TESTUSER_PWD},
            follow=True
        )

        # Check success
        self.assertTemplateUsed(
            response,
            'scionlab/ASes_overview.html',
            "Expected user page template."
        )

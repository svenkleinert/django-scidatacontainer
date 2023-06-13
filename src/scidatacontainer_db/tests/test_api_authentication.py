from django.urls import reverse
from django.contrib.auth.models import User

import uuid

from rest_framework.test import APITestCase
from knox.models import AuthToken


class ApiAuthenticationTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = str(uuid.uuid4())
        cls.user = User.objects.create_user("testuser", password=cls.password)
        cls.token = AuthToken.objects.create(cls.user)[1]

    def test_token_authentication(self):
        response = self.client.get(reverse("scidatacontainer_db:api:api-root"))
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token)
        response = self.client.get(reverse("scidatacontainer_db:api:api-root"))
        self.assertEqual(response.status_code, 200)

    def test_password_authentication(self):
        response = self.client.get(reverse("scidatacontainer_db:api:api-root"))
        self.assertEqual(response.status_code, 401)

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse("scidatacontainer_db:api:api-root"),
                                   headers={"Authorization": "Token " +
                                                             self.token}
                                   )
        self.assertEqual(response.status_code, 200)

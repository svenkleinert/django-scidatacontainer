from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings

import uuid


class AuthenticationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password = str(uuid.uuid4())
        cls.user = User.objects.create_user("testuser", password=cls.password)

    def test_password_authentication(self):
        response = self.client.get(reverse("scidatacontainer_db:ui-index"))
        index_url = reverse("scidatacontainer_db:ui-index")
        self.assertRedirects(response,
                             settings.LOGIN_URL + "?next=" + index_url
                             )

        response = self.client.post(reverse("scidatacontainer_db:ui-login"),
                                    data={"username": self.user.username,
                                          "password": self.password,
                                          "next": index_url,
                                          }
                                    )
        self.assertRedirects(response, index_url)

        response = self.client.get(index_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("scidatacontainer_db:ui-logout"),
                                   follow=True)
        self.assertRedirects(response,
                             settings.LOGIN_URL + "?next=" + index_url
                             )

        response = self.client.get(reverse("scidatacontainer_db:ui-index"))
        self.assertRedirects(response,
                             settings.LOGIN_URL + "?next=" + index_url
                             )

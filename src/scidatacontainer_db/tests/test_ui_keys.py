from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from knox.models import AuthToken


class KeysTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _post(self, url, **kwargs):
        self.client.force_login(self.user)
        response = self.client.post(url, **kwargs)
        return response

    def _get(self, url, **kwargs):
        self.client.force_login(self.user)
        response = self.client.get(url, **kwargs)
        return response

    def test_view_url_exists_at_desired_location(self):
        response = self._get("/keys/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self._get(reverse("scidatacontainer_db:ui-keys"))
        self.assertEqual(response.status_code, 200)

    def test_template_keys(self):
        response = self._get(reverse("scidatacontainer_db:ui-keys"))
        self.assertTemplateUsed(response, "scidatacontainer_db/apikeys.html")

    def test_create_keys(self):
        response = self._get(reverse("scidatacontainer_db:ui-keys"))
        self.assertContains(response,
                            "class=\"btn-close\"",
                            count=0,
                            status_code=200)

        before = len(AuthToken.objects.all())
        response = self._post(reverse("scidatacontainer_db:ui-keys"),
                              data={"create": True})
        self.assertEqual(response.status_code, 302)
        after = len(AuthToken.objects.all())
        self.assertEqual(before + 1, after)

    def test_delete_keys(self):
        self.test_create_keys()
        before = len(AuthToken.objects.all())
        digest = (AuthToken.objects.filter(user=self.user)[0]).digest

        response = self._post(reverse("scidatacontainer_db:ui-keys"),
                              data={"delete": digest})

        self.assertEqual(response.status_code, 302)
        after = len(AuthToken.objects.all())
        self.assertEqual(before - 1, after)
        self.assertEqual(0, len(AuthToken.objects.filter(digest=digest)))

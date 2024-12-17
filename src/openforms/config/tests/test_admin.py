from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory

from .factories import MapTileLayerFactory, RichTextColorFactory


@disable_admin_mfa()
class ColorAdminTests(WebTest):
    def test_color_changelist(self):
        RichTextColorFactory.create_batch(9)
        url = reverse("admin:config_richtextcolor_changelist")
        user = SuperUserFactory.create()

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)

    def test_color_detail(self):
        color = RichTextColorFactory.create()
        url = reverse("admin:config_richtextcolor_change", args=(color.pk,))
        user = SuperUserFactory.create()

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)


@disable_admin_mfa()
class MapTileLayerTests(WebTest):
    def test_map_tile_layer_changelist(self):
        MapTileLayerFactory.create_batch(9)
        url = reverse("admin:config_maptilelayer_changelist")
        user = SuperUserFactory.create()

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)

    def test_map_tile_layer_detail(self):
        map = MapTileLayerFactory.create()
        url = reverse("admin:config_maptilelayer_change", args=(map.pk,))
        user = SuperUserFactory.create()

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)

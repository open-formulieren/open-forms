"""URLs to run the tests."""
from compat import include, url

from django.contrib import admin

from hijack_admin.admin import HijackRelatedAdminMixin
from hijack_admin.tests.test_app.models import RelatedModel


@admin.register(RelatedModel)
class RelatedModelAdmin(HijackRelatedAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'hijack_field')


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^hijack/', include('hijack.urls', namespace='hijack')),
    url(r'^hello/', include('hijack.tests.test_app.urls', namespace='test_app'))
]

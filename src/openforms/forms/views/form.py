import logging

from django.http import HttpResponseRedirect

from openforms.config.models import GlobalConfiguration
from openforms.ui.views.generic import UIDetailView, UIListView

from ..models import Form

logger = logging.getLogger(__name__)


class FormListView(UIListView):
    template_name = "core/views/form/form_list.html"
    queryset = Form.objects.live()

    def get(self, request, *args, **kwargs):
        config = GlobalConfiguration.get_solo()

        render_list = not config.main_website or request.user.is_staff
        if render_list:
            if not config.main_website:
                logger.info(
                    "Rendering list view because there's no redirect target set up."
                )
            return super().get(request, *args, **kwargs)

        # looks like an "open redirect", but admins control the value of this and
        # we only give access to trusted users to the admin.
        return HttpResponseRedirect(config.main_website)


class FormDetailView(UIDetailView):
    template_name = "core/views/form/form_detail.html"
    queryset = Form.objects.live()

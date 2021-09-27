#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

from django.conf.urls import url
from django.contrib import admin

try:
    # from django 1.10 and above
    from django.urls import reverse
except ImportError:
    # until django 1.9
    from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.decorators.clickjacking import xframe_options_sameorigin

from django_yubin import models

from .mail_utils import get_attachments, get_attachment


class Message(admin.ModelAdmin):
    def message_link(self, obj):
        url = reverse('admin:mail_detail', args=(obj.id,))
        return mark_safe("""<a href="%s" onclick="return showAddAnotherPopup(this);">show</a>""" % url)

    message_link.allow_tags = True
    message_link.short_description = u'Show'

    list_display = ('from_address', 'to_address', 'subject', 'date_created', 'date_sent', 'message_link')
    list_filter = ('date_created', 'date_sent')
    search_fields = ('to_address', 'subject', 'from_address',
                     'encoded_message',)
    date_hierarchy = 'date_created'
    ordering = ('-date_created',)
    actions = ['re_send', ]

    def re_send(self, request, queryset):
        """
        Re sends a previus sent e-mail. The messages shouldn't be in the queue and
        is put in the NORMAL priority
        """
        messages_sent = 0
        for selected_mail in queryset:
            qm = models.QueuedMessage(message=selected_mail)
            try:
                qm.save()
                messages_sent += 1
            except IntegrityError:
                self.message_user(request, 'Message %s is already in the queue' % selected_mail.id)
        self.message_user(request, "%s messages had been re-sent" % messages_sent)
    re_send.short_description = 're-send selected emails'

    def get_urls(self):
        urls = super(Message, self).get_urls()
        custom_urls = [
            url(r'^mail/(?P<pk>\d+)/$',
                self.admin_site.admin_view(self.detail_view),
                name='mail_detail'),
            url('^mail/attachment/(?P<pk>\d+)/(?P<firma>[0-9a-f]{32})/$',
                self.admin_site.admin_view(self.download_view),
                name="mail_download"),
            url('^mail/html/(?P<pk>\d+)/$',
                self.admin_site.admin_view(self.html_view),
                name="mail_html"),
        ]
        return custom_urls + urls

    def detail_view(self, request, pk):
        instance = models.Message.objects.get(pk=pk)
        msg = instance.get_pyz_message()
        context = {'subject': msg.get_subject(), 'from': msg.get_address('from'), 'to': msg.get_addresses('to'),
                   'cc': msg.get_addresses('cc'),
                   'msg_text': msg.text_part.part.get_payload(
                       decode=self.is_encoded(msg, 'text_part')) if msg.text_part else None,
                   'msg_html': msg.html_part.part.get_payload(
                       decode=self.is_encoded(msg, 'html_part')) if msg.html_part else None,
                   'attachments': get_attachments(msg), 'is_popup': True, 'object': instance}
        return render(request, 'django_yubin/message_detail.html', context)

    def download_view(self, request, pk, firma):
        instance = models.Message.objects.get(pk=pk)
        msg = instance.get_pyz_message()
        arx = get_attachment(msg, key=firma)
        response = HttpResponse(content_type=arx.tipus)
        response['Content-Disposition'] = 'filename=' + arx.filename
        response.write(arx.payload)
        return response

    @xframe_options_sameorigin
    def html_view(self, request, pk):
        instance = models.Message.objects.get(pk=pk)
        msg = instance.get_pyz_message()
        msg.html_part.part._charset = 'utf-8'
        context = {'msg_html': msg.html_part.part.get_payload(decode=self.is_encoded(msg, 'html_part'))}
        return render(request, 'django_yubin/html_detail.html', context)

    @staticmethod
    def _is_encoding_header(header_name):
        return header_name in ['base64', 'quoted-printable']

    @staticmethod
    def is_encoded(msg, part='html_part'):
        """
        detect whether the part is encoded or not. We'll check for known encoding headers

        :param msg, part:
        :return:
        """
        if part == 'html_part':
            return any(Message._is_encoding_header(header[1]) for header in msg.html_part.part._headers)
        elif part == 'text_part':
            return any(Message._is_encoding_header(header[1]) for header in msg.text_part.part._headers)
        return False


class MessageRelatedModelAdmin(admin.ModelAdmin):
    list_select_related = True

    def message__to_address(self, obj):
        return obj.message.to_address

    message__to_address.admin_order_field = 'message__to_address'

    def message__from_address(self, obj):
        return obj.message.from_address

    message__from_address.admin_order_field = 'message__from_address'

    def message__subject(self, obj):
        return obj.message.subject

    message__subject.admin_order_field = 'message__subject'

    def message__date_created(self, obj):
        return obj.message.date_created

    message__date_created.admin_order_field = 'message__date_created'


class QueuedMessage(MessageRelatedModelAdmin):
    def not_deferred(self, obj):
        return not obj.deferred

    not_deferred.boolean = True
    not_deferred.admin_order_field = 'deferred'

    def message_link(self, obj):
        url = reverse('admin:mail_detail', args=(obj.message.id,))
        return mark_safe("""<a href="%s" onclick="return showAddAnotherPopup(this);">%s</a>""" % (url, obj.message))

    message_link.allow_tags = True
    message_link.short_description = u'Message'

    list_display = ('id', 'message_link', 'message__to_address',
                    'message__from_address', 'message__subject',
                    'message__date_created', 'priority', 'not_deferred')
    list_filter = ('priority', 'deferred')


class Blacklist(admin.ModelAdmin):
    list_display = ('email', 'date_added')


class Log(MessageRelatedModelAdmin):
    def message_link(self, obj):
        url = reverse('admin:mail_detail', args=(obj.message.id,))
        return mark_safe("""<a href="%s" onclick="return showAddAnotherPopup(this);">show</a>""" % url)

    message_link.allow_tags = True
    message_link.short_description = u'Message'

    list_display = ('id', 'result', 'message__to_address', 'message__subject',
                    'date', 'message_link')
    list_filter = ('result',)
    list_display_links = ('id', 'result')


admin.site.register(models.Message, Message)
admin.site.register(models.QueuedMessage, QueuedMessage)
admin.site.register(models.Blacklist, Blacklist)
admin.site.register(models.Log, Log)

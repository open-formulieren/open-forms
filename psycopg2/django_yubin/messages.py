#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template, select_template, _engine_list


def template_from_string(template_string, using=None):
    """
    Creates and returns a template for the given string.
    """
    engine = _engine_list(using)[0]
    return engine.from_string(template_string)


class EmailMessageView(object):
    """
    Base class for encapsulating the logic for the rendering and sending
    class-based email messages.
    """

    message_class = EmailMessage

    @property
    def headers(self):
        """
        A dictionary containing the headers for this message.
        """
        if not hasattr(self, '_headers'):
            self._headers = {}
        return self._headers

    def set_priority(self, priority):
        """
        sets the queue priority

        :param priority
        :type string
            now-not-queued
            now
            high
            normal
            low
        """
        if not hasattr(self, '_headers'):
            self._headers = {'X-Mail-Queue-Priority': priority}
        else:
            self._headers['X-Mail-Queue-Priority'] = priority

    def render_subject(self, context):
        raise NotImplementedError  # Must be implemented by subclasses.

    def render_body(self, context):
        raise NotImplementedError  # Must be implemented by subclasses.

    def get_context_data(self, **kwargs):
        """
        Returns the context that will be used for rendering this message.

        :rtype: :class:`dict`
        """
        return kwargs

    def render_to_message(self, extra_context=None, **kwargs):
        """
        Renders and returns an unsent message with the provided context.

        Any extra keyword arguments passed will be passed through as keyword
        arguments to the message constructor.

        :param extra_context: Any additional context to use when rendering the
            templated content.
        :type extra_context: :class:`dict`

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            attachments=None,
            cc=None
            headers=None,

        :returns: A message instance.
        :rtype: :attr:`.message_class`
        """
        if extra_context is None:
            extra_context = {}

        # Ensure our custom headers are added to the underlying message class.
        kwargs.setdefault('headers', {}).update(self.headers)

        context = self.get_context_data(**extra_context)
        return self.message_class(
            subject=self.render_subject(context),
            body=self.render_body(context),
            **kwargs)

    def send(self, extra_context=None, **kwargs):
        """
        Renders and sends an email message.

        All keyword arguments other than ``extra_context`` are passed through
        as keyword arguments when constructing a new :attr:`message_class`
        instance for this message.

        This method exists primarily for convenience, and the proper
        rendering of your message should not depend on the behavior of this
        method. To alter how a message is created, override
        :meth:``render_to_message`` instead, since that should always be
        called, even if a message is not sent.

        :param extra_context: Any additional context data that will be used
            when rendering this message.

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            attachments=None,
            cc=None
            headers=None,

        :type extra_context: :class:`dict`

        """
        message = self.render_to_message(extra_context=extra_context, **kwargs)
        return message.send()


class TemplatedEmailMessageView(EmailMessageView):
    """
    An email message view that uses Django templates for rendering the message
    subject and plain text body.
    """
    #: A template name (or list of template names) that will be used to render
    #: the subject of this message. The rendered subject should be plain text
    #: without any linebreaks. (Any trailing whitespace will be automatically
    #: stripped.) :attr:`.subject_template` will precedence over this value,
    #: if set.
    subject_template_name = None

    #: A template name (or list of template names) that will be used to render
    #: the plain text body of this message. :attr:`.body_template` will take
    #: precedence over this value, if set.
    body_template_name = None

    def _get_template(self, value):
        if isinstance(value, (list, tuple)):
            return select_template(value)
        else:
            return get_template(value)

    def _get_subject_template(self):
        if getattr(self, '_subject_template', None) is not None:
            return self._subject_template

        if self.subject_template_name is None:
            raise ImproperlyConfigured('A `subject_template` or '
                                       '`subject_template_name` must be provided to render this '
                                       'message subject.')

        return self._get_template(self.subject_template_name)

    def _set_subject_template(self, template):
        self._subject_template = template

    #: Returns the subject template that will be used for rendering this
    #: message. If the subject template has been explicitly set, that template
    #: will be used. If not, the template(s) defined as
    #: :attr:`.subject_template_name` will be used instead.
    subject_template = property(_get_subject_template, _set_subject_template)

    def _get_body_template(self):
        if getattr(self, '_body_template', None) is not None:
            return self._body_template

        if self.body_template_name is None:
            raise ImproperlyConfigured('A `body_template` or '
                                       '`body_template_name` must be provided to render this '
                                       'message subject.')

        return self._get_template(self.body_template_name)

    def _set_body_template(self, template):
        self._body_template = template

    #: Returns the body template that will be used for rendering this message.
    #: If the body template has been explicitly set, that template will be
    #: used. If not, the template(s) defined as :attr:`.body_template_name`
    #: will be used instead.
    body_template = property(_get_body_template, _set_body_template)

    def render_subject(self, context):
        """
        Renders the message subject for the given context.

        :param context: The context to use when rendering the subject template.
        :type context: :class:`dict`
        :returns: A rendered subject.
        :rtype: :class:`str`
        """
        rendered = self.subject_template.render(context)
        return rendered.strip()

    def render_body(self, context):
        """
        Renders the message body for the given context.

        :param context: The context to use when rendering the body template.
        :type context: :class:`dict`
        :returns: A rendered body.
        :rtype: :class:`str`
        """
        return self.body_template.render(context)


class TemplatedHTMLEmailMessageView(TemplatedEmailMessageView):
    """
    An email message view that uses Django templates for rendering the message
    subject, plain text and HTML body.
    """
    message_class = EmailMultiAlternatives

    #: A template name (or list of template names) that will be used to render
    #: the HTML body of this message. :attr:`.html_body_template` will take
    #: precedence over this value, if set.
    html_body_template_name = None

    def _get_html_body_template(self):
        if getattr(self, '_html_body_template', None) is not None:
            return self._html_body_template

        if self.html_body_template_name is None:
            raise ImproperlyConfigured('An `html_body_template` or '
                                       '`html_body_template_name` must be provided to render this '
                                       'message HTML body.')

        return self._get_template(self.html_body_template_name)

    def _set_html_body_template(self, template):
        self._html_body_template = template

    #: Returns the body template that will be used for rendering the HTML body
    #: of this message. If the HTML body template has been explicitly set, that
    #: template will be used. If not, the template(s) defined as
    #: :attr:`.html_body_template_name` will be used instead.
    html_body_template = property(_get_html_body_template,
                                  _set_html_body_template)

    def get_context_data(self, **kwargs):
        """
        As is quite commont to have images in an HTML e-mail add MEDIA_URL
        and STATIC_URL to the context with its full path
        """

        domain = Site.objects.get_current().domain
        ctx = super(TemplatedHTMLEmailMessageView, self).get_context_data(**kwargs)
        ctx['MEDIA_URL'] = urlparse.urljoin(domain, settings.MEDIA_URL)
        ctx['STATIC_URL'] = urlparse.urljoin(domain, settings.STATIC_URL)
        return ctx

    def render_html_body(self, context):
        """
        Renders the message body for the given context.

        :param context: The context to use when rendering the body template.
        :type context: :class:`dict`
        :returns: A rendered HTML body.
        :rtype: :class:`str`
        """
        return self.html_body_template.render(context)

    def render_to_message(self, extra_context=None, *args, **kwargs):
        """
        Renders and returns an unsent message with the given context.

        Any extra keyword arguments passed will be passed through as keyword
        arguments to the message constructor.

        :param extra_context: Any additional context to use when rendering
            templated content.
        :type extra_context: :class:`dict`

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            attachments=None,
            cc=None
            headers=None,

        :returns: A message instance.
        :rtype: :attr:`.message_class`
        """
        message = super(TemplatedHTMLEmailMessageView, self) \
            .render_to_message(extra_context, *args, **kwargs)

        if extra_context is None:
            extra_context = {}

        context = self.get_context_data(**extra_context)
        content = self.render_html_body(context)
        message.attach_alternative(content, mimetype='text/html')
        return message


class TemplatedAttachmentEmailMessageView(TemplatedHTMLEmailMessageView):
    """
    This is a sintactic sugar class to allow us to send mail messages with
    an attachment
    """

    def send(self, extra_context=None, **kwargs):
        """
        Renders and sends an email message.

        All keyword arguments other than ``extra_context`` are passed through
        as keyword arguments when constructing a new :attr:`message_class`
        instance for this message.

        This method exists primarily for convenience, and the proper
        rendering of your message should not depend on the behavior of this
        method. To alter how a message is created, override
        :meth:``render_to_message`` instead, since that should always be
        called, even if a message is not sent.

        :param extra_context: Any additional context data that will be used
            when rendering this message.

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            attachments=None,
            cc=None
            headers=None,
            filename=None,

        :type extra_context: :class:`dict`

        """
        if kwargs.get("filename") and not kwargs.get("attachment"):
            raise Exception("If filename is passed, an attachment must be provided")
        if not kwargs.get("filename") and kwargs.get("attachment"):
            raise Exception("If attachment is passed, a filename must be provided")
        message = self.render_to_message(extra_context=extra_context, **kwargs)
        return message.send()

    def render_to_message(self, extra_context=None, filename=None, attachment=None, mimetype=None, *args, **kwargs):
        """
        Renders and returns an unsent message with the given context.

        Any extra keyword arguments passed will be passed through as keyword
        arguments to the message constructor.

        :param extra_context: Any additional context to use when rendering
            templated content.
        :type extra_context: :class:`dict`

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            attachments=None,
            cc=None
            headers=None,
        :param filename: filename (with extension) of the attachment
        :param attachment: attachment content
        :param mimetype: mimetype of attachment

        :returns: A message instance.
        :rtype: :attr:`.message_class`
        """

        message = super(TemplatedHTMLEmailMessageView, self) \
            .render_to_message(extra_context, *args, **kwargs)

        if extra_context is None:
            extra_context = {}
        context = self.get_context_data(**extra_context)
        content = self.render_html_body(context)
        message.attach_alternative(content, mimetype='text/html')
        if filename and attachment:
            message.attach(filename=filename, content=attachment, mimetype=mimetype)

        return message


class TemplatedMultipleAttachmentsEmailMessageView(TemplatedHTMLEmailMessageView):
    """
    This is a sintactic sugar class to allow us to send mail messages with
    multiple attachments
    """

    def send(self, extra_context=None, attachments=None, **kwargs):
        """
        Renders and sends an email message.

        All keyword arguments other than ``extra_context`` are passed through
        as keyword arguments when constructing a new :attr:`message_class`
        instance for this message.

        This method exists primarily for convenience, and the proper
        rendering of your message should not depend on the behavior of this
        method. To alter how a message is created, override
        :meth:``render_to_message`` instead, since that should always be
        called, even if a message is not sent.

        :param extra_context: Any additional context data that will be used
            when rendering this message
        :param attachments: List of dicts with filename and attachment file, with keys 'filename', 'attachment'
        and 'mimetype'.

        Attachments example -> [{"filename": "filename.pdf", "attachment": "file-path",},...]

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            cc=None
            headers=None,

        :type extra_context: :class:`dict`
        :type attachments: :class:`list`

        """

        if isinstance(attachments, list):
            for attachment in attachments:
                if not attachment.get("filename") or not attachment.get("attachment"):
                    raise Exception("'filename', 'attachment' are mandatory for every attachment")

        message = self.render_to_message(extra_context=extra_context, attachments=attachments, **kwargs)
        return message.send()

    def render_to_message(self, extra_context=None, attachments=None, *args, **kwargs):
        """
        Renders and returns an unsent message with the given context.

        Any extra keyword arguments passed will be passed through as keyword
        arguments to the message constructor.

        :param extra_context: Any additional context to use when rendering
            templated content.
        :type extra_context: :class:`dict`
        :param attachments: List of dicts with filename and attachment file
        :type attachments: :class:`list`

        :param kwargs : mail settings
            from_email=None,
            to=None,
            bcc=None,
            connection=None,
            cc=None
            headers=None,

        :returns: A message instance.
        :rtype: :attr:`.message_class`
        """

        message = super(TemplatedMultipleAttachmentsEmailMessageView, self).render_to_message(
            extra_context, *args, **kwargs)

        if extra_context is None:
            extra_context = {}
        context = self.get_context_data(**extra_context)
        content = self.render_html_body(context)
        message.attach_alternative(content, mimetype='text/html')
        if isinstance(attachments, list):
            for attachment in attachments:
                message.attach(filename=attachment.get("filename"), content=attachment.get("attachment"))

        return message


class TemplateContextMixin(object):
    subject_template = template_from_string('{% autoescape off %}{{ subject }}{% endautoescape %}')
    body_template = template_from_string('{% autoescape off %}{{ content }}{% endautoescape %}')

    def __init__(self, subject, content):
        self.subject = subject
        self.content = content

    def get_context_data(self, *args, **kwargs):
        data = super(TemplateContextMixin, self).get_context_data(*args, **kwargs)
        data.update({
            'subject': self.subject,
            'content': self.content,
        })
        return data


class BasicEmailMessageView(TemplateContextMixin, TemplatedEmailMessageView):
    pass


class BasicHTMLEmailMessageView(TemplateContextMixin, TemplatedHTMLEmailMessageView):
    html_body_template = template_from_string(
        '{% autoescape off %}{{ content|linebreaks }}{% endautoescape %}')


class BasicHTMLAttachmentEmailMessageView(TemplateContextMixin, TemplatedAttachmentEmailMessageView):
    html_body_template = template_from_string(
        '{% autoescape off %}{{ content|linebreaks }}{% endautoescape %}')

    def __init__(self, subject, content, attachment, filename, mimetype):
        super(BasicHTMLAttachmentEmailMessageView, self).__init__(subject, content)
        self.attachment = attachment
        self.filename = filename
        self.mimetype = mimetype

    def render_to_message(self, *args, **kwargs):
        msg = super(BasicHTMLAttachmentEmailMessageView, self).render_to_message(*args, **kwargs)
        msg.attach(filename=self.filename, content=self.attachment, mimetype=self.mimetype)
        return msg

.. _developers_csp:

Content Security Policy (CSP)
=============================

    Content-Security-Policy is the name of a HTTP response header that modern browsers
    use to enhance the security of the document (or web page). The
    ``Content-Security-Policy`` header allows you to restrict how resources such as
    JavaScript, CSS, or pretty much anything that the browser loads.

    -- `CSP Quick Reference Guide`_

Open Forms supports (fairly) strict CSP configurations, which happen to be required in
environments implementing :ref:`DigiD authentication<configuration_authentication_index>`.

Summarized, the Open Forms CSP protects against Cross Site Scripting (XSS) by blocking
unsafe constructs, such inline scripts, use of ``eval`` and inline styles.

This section describes the rationale behind the policies in Open Forms when Open Forms
serves the end-user forms *and* the considerations for third parties who
:ref:`embed <developers_sdk_embedding>` forms using the SDK.

Basic mechanism
---------------

The idea behind CSP is that when an end-user visits a page in their browser, the
application serving that page sends a HTTP Header describing the security policy.
Browser implementations are then responsible for acting according to this policy.

This way, the application is able to mark which *resources* are expected/required for
the application to work, and the browser blocks anything that is unexpected and
potentially dangerous.

The goal should always be to define a policy that is as strict as possible.

Open Forms CSP
--------------

Open Forms itself provides pages for end-user to fill out forms, so CSP is relevant.

The policy is built based on:

* any resources served by the domain serving the page are allowed (CSS, JS, fonts,
  images...). These are static assets backed by trusted Open Forms source code.

* additionally, we allow assets from the SDK base URL, i.e. the domain where the SDK is
  hosted. This *may* be different from the Open Forms backend domain and is up to the
  service provider offering Open Forms.

* For images, we also allow the services from `PDOK <https://www.pdok.nl/over-pdok>`_,
  required for the maps components.

* For images, we also allow ``data:`` URIs, used by the map and signature component.

To make some aspects that are blocked explicit:

* No ``eval`` is allowed.

* Inline scripts are blocked. In certain places inline scripts are needed, which operate
  via the CSP nonce mechanism.

* Inline styles are blocked. Open Forms passes the nonce to the SDK for WYSIWYG content
  which may contain inline styles so that it can be post-processed. More details about
  this in :ref:`developers_csp_wysiwyg`.

* Third party CDNs are blocked.

.. _developers_csp_sdk_embedding:

Embedding using the SDK
-----------------------

The :ref:`SDK <developers_sdk_index>` is developed with care to be usable in strict CSP
environments. All source code is bundled into Javascript, CSS and other static assets.
Where relevant, external dependencies have been included in the SDK bundle itself - we
do not rely on external CDNs (such as the Formio CDN, Google Fonts...).

**CSP requirements**

* The domain where the SDK is hosted must be included in the ``default-src``, otherwise
  your application cannot load the Javascript, CSS, fonts or image assets.

* The ``img-src`` requires ``https://service.pdok.nl/``, otherwise map components break.

* The ``img-src`` requires ``data:``, otherwise map and signature components break.

**CSP and WYSIWYG**

Some form design relies on WYSIWYG editors, which results in HTML blobs in API endpoint
resources that potentially have inline style (``<span style="...">...</span>``). The SDK
uses React's |dangerouslySetInnerHTML|_ for this content.

One of the SDK :ref:`embed options <developers_sdk_embedding_options>` is the
``CSPNonce``. If embedding pages include this, then the WYSIWYG content will be
post-processed to include an inline ``<style>`` tag with the nonce. See
:ref:`developers_csp_wysiwyg` for a description of the mechanism involved.

You may also include ``unsafe-inline`` in your ``style-src``, but be aware this applies
to the entire page and we recommend using the ``CSPNonce`` embed option instead.

Failure to do any of these will result in inline styles being ignored by the browser.

.. |dangerouslySetInnerHTML| replace:: ``dangerouslySetInnerHTML``
.. _dangerouslySetInnerHTML: https://reactjs.org/docs/dom-elements.html#dangerouslysetinnerhtml

.. _developers_csp_wysiwyg:

WYSIWYG, async requests and CSP
-------------------------------

Content Security Policies are a complex topic by themselves, and introducing certain
features only compounds this further.

Combining a strict CSP with WYSIWYG editors and Single-page App (SPA) architectures
requires some special attention.

WYSIWYG editors offer rich-text formatting to content editors and generally result in
plain HTML being stored in the database as a result. Because of the editor
implementation details, popular solutions (like TinyMCE, CKEditor...) apply styles by
wrapping the content in ``<span>`` elements with inline style attributes. However,
inline style attributes are typically blocked by CSP, as they require the
``unsafe-inline`` directive, which is quite a hefty solution for a relatively small
use case.

SPAs are usually implemented in Javascript and operate by making asynchronous HTTP
requests to an (external) API to retrieve the data. They then render the retrieved
data. The SPA itself can usually be implemented entirely without inline styles or inline
scripts. However, when combined with WYSIWYG editors, part of the API response data
contains HTML with inline styles which must be rendered in an "unsafe" manner (i.e.
render without automatic escaping to prevent XSS).

Furthermore, the CSP mechanism allows for nonces - these are essentially
"(near) impossible-to-guess" random values. The page requested by an end-user and sent
to the browser includes this nonce in the Content-Security-Policy header, and adds it to
any allowed inline scripts or styles, such as the script to initialize the SDK. That
nonce is valid for anything happening on the page - even with asynchronous requests and
SPAs. On page refresh, the end-user receives a different nonce value.

Open Forms does support WYSIWYG in such situations by post-processing the HTML from
WYSIWYG content, relying on the following algorithm:

1. User requests page which embeds the form/SDK
2. Embedding page generates a CSP nonce
3. Embedding page templates out the inline SDK script, including the ``CSPNonce`` embed
   option
4. Embedding page + Content-Security-Policy header is sent to the browser of the user
5. The SDK initializes, given the CSP nonce option.
6. For any API call made by the SDK to the Open Forms API:

    1. Include the ``X-CSP-Nonce`` HTTP request header
    2. Open Forms API endpoint processes request and retrieves response data
    3. Open Forms API endpoint determines which subset of fields require post-processing
    4. For every field which requires post-processing:

        1. Read the CSP Nonce value from the request header
        2. Parse the HTML
        3. For every node in the HTML:

            1. Collect the inline styles
            2. Read or generate a unique HTML ID for the node
            3. Write a CSS rule for the (generated) HTML ID and extracted styles to a
               ``<style>`` element
            4. Remove the inline ``style`` attribute
            5. Set the HTML ``id`` attribute

        4. If there are extracted styles, set the ``nonce`` value on the ``style`` element
        5. Merge the ``style`` element and the modified HTML

As an example, the following HTML with a nonce of ``r@nd0m``:

.. code-block:: html

    <p>This is some markup.</p>
    <p>It has <span style="color: red;">inline</span> styles.</p>

Results in post-processed output of:

.. code-block:: html

    <style nonce="r@nd0m">
        #nonce-b9e9b8a5fcbcf50da1ec38714cd11e73-someRandomString> {
            color: red;
        }
    </style>
    <p>This is some markup.</p>
    <p>It has <span id="nonce-b9e9b8a5fcbcf50da1ec38714cd11e73-someRandomString>">inline</span> styles.</p>


**How do we keep this secure?**

* We explicitly mark WYSIWYG fields as post-processable, rather than applying the
  post-processing globally. This works with an opt-in mechanism and is easily auditable.

* The embedding page controls the value of the nonce. If correctly implemented,
  attackers can not guess this value. Additionally, the embedding page chooses to pass
  this value to the SDK initialization.

* The SDK code itself must opt-in to use ``dangerouslySetInnerHTML`` and only does so
  on known WYSIWYG content, making this easily auditable.

* The post-processing is limited to detecting inline ``style`` *attributes*. Any inline
  ``<script>`` or ``<style>`` tags added by malicious content editors do not receive the
  nonce, and continue being blocked by the CSP of the page.

* Extracted styles are copmiled as CSS rules, targetting elements via their HTML ID. The
  generated ID is based on the value of the nonce and a unique, implementation-specific
  suffix for every node. This makes it near impossible that an ID will collide with
  statically defined CSS rules, effectively scoping the CSS only to the WYSIWYG content.

.. _CSP Quick Reference Guide: https://content-security-policy.com/

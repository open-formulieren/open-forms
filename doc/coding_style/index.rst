============
Coding style
============

Below you can find some best practices to maintain a good coding style. There
are detailed coding style guides for the `frontend <coding_style_frontend>` and
the `backend <coding_style_backend>`.

Best practices
==============

HTML
----

* Write semantic HTML before styling.
* Style your HTML, don’t HTML your style.
* Don’t put content in ``master.html``, only put boilerplate/scaffolding here.
* Use `inclusion tags`_ for reusable components and blocks otherwise.
* Wrap components/logical page blocks/standalone sections in ``{% block %}`` tags.
* Respect the `coding style <coding_style_frontend>`.
* If it makes sense to divert, divert.

.. _inclusion tags: https://docs.djangoproject.com/en/stable/howto/custom-template-tags/#inclusion-tags


CSS/SASS
--------

* Bootstrap is only allowed for quick prototyping (you discard it later).
* Adhere to the `BEM`_ naming standard.
* Match component (file)names to Django template blocks.
* Maximum 1 BEM block per sass file.
* Only select using (BEM) class names (``.block__element``), avoid using tag/id
  (Matching id's breaks reusability, matching tags breaks flexibility).
* WYSIWYG is an exception (customers don’t type content__heading--primary).
* The Block (**B**EM) cannot set margin on itself, only on children. This avoids
  spacing issues.
* Use Neat mixins for (responsive) grids. Avoid complex overdoing mixins (e.g. Bourbon).
* Respect the `coding style <coding_style_frontend>`.
* Compile to CSS and keep the compiled css in version control.
* If it makes sense to divert, divert.

.. _BEM: http://stackoverflow.com/documentation/css/5302/bem#t=201608181228046431355


Javascript
----------

* These libraries/tools are deprecated - better alternatives exist:
  - Bootstrap
  - Bower
  - Django Pipeline/Compressor
  - jQuery
  - RequireJS
* Keep the existing, working setup in older projects.
* Match component (file)names to Django template blocks.
* Write (object oriented) `ES6`_ or newer.
* No dialects (typescript/coffeescript).
* Use a bundler (jspm or webpack) to manage dependencies/transpiling.
* gulp is our task runner (manage.py for frontend).
* Keep the JS source in the `static` folder per Django app.
* Respect the `coding style <coding_style_frontend>`.
* If it makes sense to divert, divert.


.. _ES6: http://es6-features.org/

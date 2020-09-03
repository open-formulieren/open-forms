.. _coding_style_frontend:

=====================
Frontend coding style
=====================

Shortcuts:

* :ref:`html`
* :ref:`sass`
* :ref:`javascript`


.. _html:

HTML
====

Common
------

* Inline style is evil

  .. code-block:: html

    <p style="color: red;">
    Inline style cannot be cached.<br />
    Inline style is difficult to overwrite.<br />
    Inline style makes HTML less readable.<br />
    Inline style is harder to spot.<br />
    </p>

* Inline script is evil (except Google Analytics)

  .. code-block:: html

    <script>
        console.log('Inline script cannot be cached.');
        console.log('Inline script makes HTML less readable.');
        console.log('Inline script blocks loading of page.');
    </script>

* Style your HTML, don't HTML your style (avoid adding divs for style)

  .. code-block:: html

    <div class="wrapper">
        <div class="inner">
            <div class="content">
                <p class="text>
                    All these tags have no acutual meaning.<br />
                    Consider HTML as data model, it should represent data, not style placeholders.<br />
                    Good practice is to write you HTML first, based on the structure of the content, then style.<br />
                    It's almost never needed to add more tags, have you tried :before and :after yet?<br />
                </p>
            </div>
        </div>
    </div>

* Empty newline at the end of the file.

Indentation
-----------

* Indent with 4 spaces

  .. code-block:: html

    <html>
        <body>
        </body>
    </html>

* Indent HTML and template tags. (except ``{% block %}`` on root level).

  .. code-block:: django

    {% block content %}
    <article>
        {% if show_header %}
            {% block article__header %}
                <header>
                </header>
            {% endblock article__header %}
        {% endif %}
    </article>
    {% endblock content %}


Data-attributes
---------------

* (Meta)data should be stored in data- attributes.

  .. code-block:: html

    <article data-article-id="1">...</article>

* Variables should be passed using data-attributes as well. They are no excuse for inline script.

  .. code-block:: html

    <article data-some-variable="1">...</article>


Elements
--------

* Avoid the ``id`` attribute, unless there's a good reason.

  .. code-block:: html

    <article id="article-1" />  <!-- wrong -->
    <article class="article" data-id="1" /> <!-- better -->

    <!-- ok, since it's useful in unit tests with WebTest -->
    <form id="submit-article">...</form>

* Use `semantic tags`_ like ``<main>``, ``<nav>``, ``<article>``, ``<section>``,
  ``<aside>``, ``<footer>`` instead of meaningless ``<div>`` s.

  .. code-block:: html

    <!DOCTYPE html>
    <html>
        <head></head>
        <body>
            <main>
                <nav>
                </nav>

                <article>
                    <header></header>
                    <section></section>
                    <section></section>
                    <footer></footer>
                </article>

                <footer>
                </footer>
            </main>
        </body>
    </html>


.. _semantic tags: http://www.hongkiat.com/blog/html-5-semantics/


.. _sass:

Sass
====

Common
------

* Readability comes first
* Annotate when useful

Globals
-------

* Avoid global styling - leave that to the CSS reset.
* Limit global configuration to:
  - Grid
  - Breakpoints
  - Colors
  - Font definitions

Indentation
-----------

* Indent using two spaces

  .. code-block:: scss

    .block {
      width: 100%;
    }

Nesting
-------

* Namespace BEM blocks

  .. code-block:: scss

    .block {
      // Everything should be nested inside .block
      // This makes sure no elements "bleed" to the global scope
      .block__element {
        ...
      }
    }

* Nest maximum 3 levels deep

  .. code-block:: scss

    .block {             // One
      .block__element {  // Two
        &:hover {        // Three
          color: #0000FF;
        }
      }
    }

Newlines
--------

* 1 empty newline after mixin/variable block

  .. code-block:: scss

    .block__element-one {
    }

    .block__element-two {
    }

* Empty newline at the end of the file.

Order
-----

* Block modifiers come before block elements, element modifier come after the
  element. Example:

  .. code-block:: scss

    .block {  // .block is the basic element
      // --active is the modifier for .block, and should be grouped with .block
      &.block--active {
      }

      // __element is a child element dependent on .block
      .block__element {
      }

      // --disabled is the modifier for .block__element, and should be grouped with .block__element
      .block__element--disabled {
      }
    }

* Mixins always come first, and then group attributes logically.

  Mixins come first so that their behaviour can still be overridden. Logical
  groups are for example text styling and borders.

  .. code-block:: scss

    .block {
      @include span-columns(4 of 12);

      font-size: 18px;
      color: #FFF;

      border: solid 1px #FFFF00;
      border-radius: 5px;
    }


Selectors
---------

* Use `BEM`_ class naming.

  .. code-block:: scss

    // BEM (Block, Element, Modifier) is a structured naming convention for CSS classes
    // A double underscore (__) separates the element from a block
    // A double dash (--) separates the modifier from the block or element
    // These fixed patters make it also possible to be parsed by (JavaScript) code

    .block {  // A block describes a standalone component
      &.block--modifier {  // A modifier describes a state or theme for eithe a block or an element
      }

      .block__element {  // An element is a component that depends on a block
      }

      .block__element--modifier {  // This modifier desrcibes the state or theme for an element
      }
    }

* Maximum one BEM block per file

  .. code-block:: scss

    // file src/openforms/sass/components/blocks/_block.scss

    .block {  // That's it, no more blocks in this file
      // ...
    }

* Only select using (BEM) class names (.block__element), not using tag/id.

  .. code-block:: scss

    div {  // Bad, tags may change an that would break our code
    }

    article { // Also bad, event semantic (descriptive) tags may change
    }

    h1 {  // Also bad, a marketeer may drop in and ask you to change it into an h2 (design will break and designer will be mad)
    }

    #content {  // Bad, we can't repeat this anymore because id's must be unique
    }

    .content {  // Better, content is our block
      .content__heading {  // Better, content__heading is a valid class name for an h1, or h2 in block content
      }
      .content__body {  // This could be a class name for a paragraph in block content
      }
    }

    .wysiwyg-content {
      h1 {  // Necessity breaks rule - WYSIWYG editors don't adhere to BEM.
      }
    }


.. _BEM: http://stackoverflow.com/documentation/css/5302/bem#t=201608181228046431355


Variables
---------

Privatize variables by assigning them on top of the module.

.. code-block:: scss

  $article-color: $color;  // We copy the contents of a global variable into a private one
  $article-font: $font;    // This allow us easily "fix" the values and reuse our component

  .article {
    color: $article-color;  // We use private values here
    font-family: $article-font;
  }

.. _javascript:

JavaScript
==========

Common
------

* Readability first
* Annotate when useful - e.g. input for functions/methods and return values/types.

  .. code-block:: javascript

    /**
     * Helper method to add an additional class name with a specific modifier (--modifier) to a BEM (Block Element Modifier) element
     * A modifier class is created for each of the existing class names
     * Class names containing "--" (modifier pattern) are discarded
     * Double class names are prevented
     * @param {HTMLElement} node The block/element to append the class name to (block, block__element)
     * @param {String} modifier The name of the modifier (--name)
     */
    function addModifier(node, modifier) {
    }

Indentation
-----------

* Indent using 4 spaces

Classes
-------

* Use TitledCamelCase for class names

  .. code-block:: javascript

    class Header {  // Bonus points: match class to BEM block name
    }

Conditionals
------------

* Put a space between the operator and brackets

  .. code-block:: javascript

    if (foo === 'bar') {
        // ...
    }

Constants
---------

* Use the ``const`` keyword
* Use UPPERCASE
* Put constants at the top of the module, below the imports

  .. code-block:: javascript

    import {Foo} from 'bar.js';

    const MY_AWESOME_CONSTANT = 'foo';

Event binding
-------------

* Separate wiring events with event handlers from logic

  .. code-block:: javascript

    class Handler {

      /**
       * We separate "wiring" from the main logic so we can resure the logic
       */
      setUpOpen() {
          BUTTON_OPEN.addEventListener('click', this.open.bind(this));
      }

      /**
       * We can now reuse `this`
       */
      open(event) {
          // `this` points to the `handler` instance
      }

    }

Functions
---------

* use camelCase names
* no space between ``function`` and brackets
* opening bracket goes on the same line, closing bracket has its own line

Example:

  .. code-block:: javascript

    function fooBar(arg1, arg2) {
        // ...
    }

Line breaks/newlines
--------------------

* watch the line length: soft limit on 79 characters, hard limit on 119
* no newline inside logical block:

  .. code-block:: javascript

    function doFooBar() {

        // ^ Bad, keep related code together
        console.log('indent', 4, 'spaces');
    }

* Empty newline after method/variable block.

  .. code-block:: javascript

    function doFooBar() {
        let fooBar = 'foobar';

        console.log(fooBar);
    }

* 2 empty lines after top level function/class/block

  .. code-block:: javascript

    const FOO = 'foo';
    const BAR = 'bar';


    function doFooBaz() {  // 2 Empty newlines after a block of constants
        console.log('foobaz');
    }


    class Foo {  // 2 Empty newlines after a top level function
        constructor() {
            super();
            this.doBar();
        }

        doBar() {  // 1 Empty newline after method
            let bar = new Bar();
        }
    }


    class Bar {   // 2 Empty newlines after a class
        constructor() {
            super();
            this.doBar();
        }

        doBar() {
            let bar = new Bar();
        }
    }

* Empty newline at the end of the file

Variables
---------

* Use the ``let`` keyword instead of ``var``
* Group variable declarations together
* Use camelCase names

Example:

.. code-block:: javascript

  function doFooBar() {
      let foo = 'foo',
          bar = 'bar',
          fooBar = foo+bar;

      console.log(fooBar);
  }

Tests
-----

* Name the test files ``foo.spec.js``. ``.spec`` indicates that it's a test file

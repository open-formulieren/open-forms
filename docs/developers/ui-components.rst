.. _developers_ui_components:

======================
Creating UI components
======================

UI components are (reusable) logical building blocks to build user interfaces. Some
obvious examples are buttons and links. More complex examples are footers with navigation
elements or a form field input with label, input and validation errors.

Development of (new) UI components in Open Forms is subject to some guidelines and
rules, with the goal of:

* contribute to good accessibility
* make it possible to *theme* them, so appearance can be tailored to the organization
* being reusable in similar but different contexts
* make it easy to maintain the code

The next sections describe how to approach creating or modifying UI components.

Check for existing community components
=======================================

The `NL Design System components <https://www.nldesignsystem.nl/componenten/>`_
catalogue already lists a large number of components that may fit your requirements.

You should always check first if there's anything suitable. This can lead to an easily
re-used community component, or at a minimum provide resources about how to implement
such a component.

Make sure to read up on how other organizations use components, which design constraints
they have taken into consideration and where the variation lies if different community
implementations exist.

If nothing exists that is readily usable, you can proceed with implementing it yourself,
but you should still keep in mind the NL DS research so that future implementations can
converge on a single approach. You can explore whether the NL DS community is open to
contributions for such a component if you want too.

Building a component from scratch
=================================

Composition
-----------

Often you need to build a higher level component that's composed of other lower level
components. That's normal - the obvious low-level components like buttons and links are
seldomly used in isolation, and we encourage re-using these instead of reinventing the
wheel.

Consider the footer example:

.. code-block:: html

    <footer class="openforms-footer">
      <a href="#" class="utrecht-link">Link 1</a>
      <a href="#" class="utrecht-link">Link 2</a>
      <a href="#" class="utrecht-link">Link 3</a>
    </footer>

This simple example captures the essence well: the appearance of an individual link
should be consistent with other links on the page, so you re-use the ``utrecht-link``
component.

However, the footer gets an application-specific class name, so that the layout and
appearance (such as flex display with left or center alignment, background color...)
can be specified on that element.

Markup
------

Use semantic HTML, and try to use only what's necessary. Avoid wrapper ``div`` and
``span`` elements if you can - often with Flexbox and CSS Grid styling you can get quite
far for layout management.

If you're not yet familiar with the implicit accessible roles of elements, take some
time to do the research. E.g. it may seem obvious to use a ``nav`` element, but if this
results in multiple such elements on a page, additional work is needed to give them
distinctive accessible labels.

The question "How would this appear to a screenreader" should always be at the forefront
when writing HTML.

Block-Element-Modifier (BEM)
----------------------------

`BEM <https://getbem.com/>`_ is a methodology for reusable components.

**Blocks**

For the CSS and CSS class names, the BEM methodology is used. In a nutshell, this means
the outer element gets a ``.my-block`` classname that encapsulates the component and
is the outer CSS target selector.

Example:

.. code-block:: html

    <footer class="openforms-footer">
        ...
    </footer>

.. tip::

    * You should try to limit the number of different blocks that exist in a codebase.
    * Avoid using extremely specific blocks that cannot be reused in other places.

**Elements**

The element can contain zero or more child elements, which get a ``.my-block__element-1``
or ``.my-block__element-2`` class name. They can exist anywhere in the HTML tree, they
are not limited to direct children - see the example below.

A child element cannot exist / does not have meaning without its block parent.

For example:

.. code-block:: html

    <footer class="openforms-footer">
        <ul class="openforms-footer__group">
            <li class="openforms-footer__item">
                <a href="#" class="utrecht-link">Some link</a>
            </li>
        </ul>

        <ul class="openforms-footer__group"> ... </ul>

        <ul class="openforms-footer__group"> ... </ul>
    </footer>

Note that in HTML ``openforms-footer__item`` is a child element of
``openforms-footer__group``, but from the BEM names and styling you cannot infer this
relationship.

.. warning::

    You can have only **one** occurrence of the `__` separator. A class name like
    ``.block__element__nested`` is not valid according to BEM, and a red flag that
    your class names are mimicking your HTML structure.

.. tip::

    It's okay to combine an element and block class name, e.g.
    ``utrecht-link openforms-footer__link`` can make sense. The styles from the element
    are then scoped to when a link is a child of the block element.

**Modifiers**

Modifiers indicate variants of a block and/or element. The double dash (``--``)
separator is used: ``.block--modifier`` and ``.block__element--modifier``.

Modifiers can be applied to both blocks and elements, e.g.:

.. code-block:: html

    <footer class="openforms-footer openforms-footer--vertical">
        <ul class="openforms-footer__group openforms-footer__group--compact">
            ...
        </ul>
    </footer>

.. warning::
    A modifier is always relative to its base block or element, meaning you must include
    that base class name too. ``<a href="#" class="utrecht-link--html-a">...</a>`` is
    incorrect usage, instead it must be:
    ``<a href="#" class="utrecht-link utrecht-link--html-a">...</a>``

**SCSS helpers**

Most of our repositories have helpers to build the correct BEM class names:

* ``formio-renderer`` -> use ``@/scss/bem``
* ``formio-builder`` -> no helper available
* remainder -> use ``microscope-sass/lib/bem``, but keep in mind that ``microscope-sass``
  is deprecated and being phased out.

Example usage:

.. code-block:: scss

    @use '@/scss/bem';

    .openforms-footer {
        display: flex;
        flex-direction: row;

        @include bem.modifier('vertical') {
            // modifier styles
            flex-direction: column;
        }

        @include bem.element('group') {
            // group styles
            list-style: none;
            margin: 0;
            padding: 0;

            @include bem.modifier('compact') {
                // group modifier styles
            }
        }

        @include bem.element('item') {
            // item styles
        }
    }



CSS rules
---------

**BEM and spacing**

Blocks should ideally never define margins. For spacing control, you should use paddings
instead. A block is the atomic unit and is synonym to "component". Defining margins
messes with the layout when a block is used in a larger UI and can lead to unintended
wrapping.

Elements don't have this restricting, because they are contained within their block and
not expected to leak outside their container.

**Design tokens and CSS variables**

Theming support is implemented using CSS custom properties (a.k.a. variables). Certain
appearance properties may be relevant for custom themes, such as colors, spacing, font
family and font-style.

Design tokens are a mechanism to provide values for these styles - design tokens are
typically defined in JSON, which compiles down to (amongst other formats) CSS.

An example:

.. code-block:: json

    {
        "of": {
            "footer": {
                "background-color": {"value": "transparent"},
                "color": {"value": "#000000"},
                "group": {
                    "compact": {
                        "padding-block-start": {"value": "4px"}
                    }
                }
            }
        }
    }

Gets compiled to:

.. code-block:: css

    .openforms-theme {
        --of-footer-background-color: transparent;
        --of-footer-color: #000000;
        --of-footer-group-compact-padding-block-start: 4px;
    }

Each component can only consume design tokens that it "owns" - you may not consume
other tokens that happen or are likely to have the same value:

.. code-block:: scss
    :caption: Valid example

    .openforms-footer {
        background-color: var(--of-footer-background-color);
        color: var(--of-footer-color);
    }

.. code-block:: scss
    :caption: Invalid example

    .openforms-footer {
        background-color: var(--of-color-primary);
        color: var(--of-color-text);
    }

This minimizes the dependencies on other components/tokens structure.

Theme builders that create the design tokens can opt to use these references to common
or brand tokens, but this also leaves the flexibility to fine tune the exact appearance
of each component.

**Design tokens and BEM**

Design tokens and BEM work well together, because they create a natural hierarchy. If
you have a ``component`` (or, in BEM-terms, a block), this is the name after the ``of``
namespace. Modifiers and elements are additional nodes.

For example, you can have the following token name patterns:

* ``of.component.property``
* ``of.component.block-modifier.property``
* ``of.component.element.property``
* ``of.component.element.element-modifier.property``
* ``of.component.block-modifier.element.property``
* ``of.component.block-modifier.element.element-modifier.property``
* ``of.component.block-modifier.ui-state.property``
* etc.

where ``property`` is a (CSS) property like ``color`` or ``padding-inline-start``,
and ``ui-state`` can be states like ``hover``, ``focus``...

**Use logical properties**

To be prepared for other text directions than left-to-right and top-to-bottom, use the
logical properties for styling instead of their literal orientations.

As a quick example:

* Use ``margin-block-start`` instead of ``margin-top``.
* Use ``margin-block-end`` instead of ``margin-bottom``.
* Use ``margin-inline-start`` instead of ``margin-left``.
* Use ``margin-inline-end`` instead of ``margin-right``.

Updating existing code
======================

The Open Forms codebase started out from a prototype, and over the past 3 or more years,
we have gained a lot more insights and experience. On top of that, technology keeps
evolving and newer browser features may be available now that weren't at the time.

So, when updating existing code, whether that's refactoring or making enhancements,
take a critical look at the existing code and the surrounding code. Especially if you
see the last change to that code happened 2+ years ago!

Ask yourself the following questions, and do the necessary research if you don't know
the answers:

* Is all of this markup/CSS necessary? Can we slim it down?
* How is this experienced by screenreader users? Is the accessibility correct?
* Do we need custom markup/CSS, or can we refactor this by using existing NL DS components?
* Are there themeable aspects that currently don't have design tokens? Is the design token
  usage correct?
* If I make changes, can I do this in a backwards compatible way?

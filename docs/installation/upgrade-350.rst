.. _installation_upgrade_350:

===================================
Upgrade details to Open Forms 3.5.0
===================================

Open Forms 3.5.0 is a minor, backwards compatible feature release. However, the changes
introduced in this release require some attention to prevent accidents.

Logic engine rework for improved performance
============================================

.. warning:: Extensively test your existing forms on the test environment before
   upgrading in production.

The big feature in this release is our reworked architecture for the logic engine
integration. Historically, Open Forms has supported two logic variants:

* "component" or "frontend" logic, configured through the "Advanced" tabs on components.
  It only controls the visibility of a component.
* "backend" logic, where advanced trigger conditions and actions can be set up that
  control the form flow, such as blocking submission, marking steps as not applicable,
  evaluating DMN and/or service fetch...

The first reacts immediately when the user fills out form fields, while the latter
required a round-trip to the server which replied with the updated form (step)
configuration. This round-trip can be quite slow, especially when compared to the
frontend logic that runs in the browser of the user.

Long story short, we've been able to make a number of frequently used backend logic
configurations in the frontend, eliminating the server round trip, which leads to a much
snappier user experience because the logic evaluation is very fast this way.

Your existing forms will keep using the legacy logic evaluation, and you can opt-in to
the new logic evaluation in the form settings. We recommend enabling both the new
logic evaluation and the new renderer at the same time.

When you enable the new logic evaluation, Open Forms will analyse your logic rules when
the form is being saved. It will determine which rules provide input and output for
other rules. Based on this information, the rules will be re-ordered and assigned to the
relevant form steps. This means that for every step in the form, only the logic rules
relevant to it will be evaluated.

Note that it is possible to enable new logic evaluation without the new renderer, in
which case forms will only benefit from the per-step execution of rules. Frontend
execution of logic rules is only possible with the new renderer.

.. note:: Before you can enable the new logic evaluation for existing forms, you must
   remove the "trigger from step" option for each rule that has it set. Open Forms will
   determine this information automatically.

.. tip:: Before you convert existing forms, it's best to make a copy of the form and try
   out the changes in that copy. You cannot easily revert back to an older version, as
   the order of the logic rules is automatically rewritten in the new logic evaluation.

New forms you add default to having the new logic evaluation and renderer enabled, but
if you know you'll run into problems, you can disable these.

What's the catch?
-----------------

This kind of architectural rework does not come for free. We've been working towards
this end-result since Open Forms 3.1.0 "Lente" a year ago and had to make sure our
changes didn't break existing forms. There have been bugs because of this rework, and
there will likely be more. Please report any issues you encounter!

Our goal is to have the exact same results when the logic is evaluated on the frontend
as on the backend. This is also essential for the input validation. During our own
testing we already identified some edge cases where this is not the case, and those
are being fixed as bugs, but there's a chance with complex forms that we missed more
edge cases - the amount of possible combinations is very high and making this bug-free
at this stage is really hard. You may encounter broken forms when you opt-in to the new
logic evaluation.

Not all logic constructions can be evaluated in the frontend - in those cases, Open
Forms will automatically revert back to the round-trip evaluation. The following cases
are not compatible with frontend evaluation:

* using template expressions (e.g. `Child: {{ firstName }}`) in component configuration
* using DMN evaluation, because server-to-server communication is required
* using service fetch, because server-to-server communication is required
* using user-defined variables as options input for radio, select and selectboxes components
* using logic rules with a "variable synchronization" action
* using logic rules with a variable action on a user-defined variable
* using date validation relative to another variable

Note that as soon as one such case is present for a logic step, it affects the whole
step.

.. warning:: In the new logic evaluation mode, we detect invalid logic expressions, most
   notably rules that have circular dependencies. Those are rules where the outcome of
   one rule affects the input of one or more other rules that ultimately again affect
   the input or outcome of the original rule. These rules cannot be supported as they
   lead to infinite loops. We provide tools to detect and report these in existing forms.

Future plans
------------

In Open Forms 4.0, which will be next version after 3.5, we will:

* remove support for the old renderer. Every form will automatically have the
  "new renderer" then.
* remove support for the legacy logic evaluation. Every form will use the "new logic
  evaluation".
* clean up how "clearing of values" works, which will lead to a behaviour change in some
  situations. More details will follow and we aim to provide detection tooling in the
  next few months.

Of course we will monitor and fix bugs in the coming months to make this possible, and
we will work on tooling to make this upgrade as smooth as possible.

We also have already identified some areas where we can further optimize the logic
evaluation, but we'll have to prioritize that based on the commonly used patterns that
would benefit the most from it. Our top priority will be stability and correctness by
eliminating all the bugs that get reported.

=====================
Children prefill flow
=====================

Configuration
==========================

First the following must be configured:

:ref:`Family members configuration <configuration_prefill_family_members>`: to retrieve
the children data.


Form
==============

1. Create a form with the name *Children flow*

2. Click on the **authentication** to expand and choose *Demo BSN*.

3. Click on the **Steps and fields** tab.

**Step 1**

4. In the menu on the left, add **Step** and choose **Make a new form definition**. Give
   the name *children step 1*.

5. Scroll to **fields**.

6. Click **Special fields** and drag a **children** field in the form.

7. Click on **Save** to save the component.

8. In the properties of the first tab (*basic*) enable **Allow selection** (this allows
   the user to select children during the form submission).

**Step 2**

9. In the menu on the left, add **Step** and choose **Make a new form definition** again.
   Give the name *children step 2*

10. Scroll to **fields**.

11. Click **Special fields** and drag a **repeating group** field in the form. Give the 
    name *Extra child details* and click on **Save**.

12. From the **Special fields** drag a **BSN** field in the form. Mark it as a read-only
    field and click on **Save**.

13. Click on the form fields and drag a **textfield** field in the form. Five it the name
    *Child name* and mark it as read-only field. Click on **Save**.

14. From the form fields drag a **Radio** field in the form. Give it the name *Goes to school*
    and add the values *yes* and *no* as the available options. Click on **Save**.

15. Click on **Save** to save the form.

**Logic action**

16. Click on the **Logic** tab.

17. Click on the **Add rule** and choose the advanced one. The rule should be a simple *true*
    in order to always trigger the following action.

18. Click on the **Add action** and choose *Synchronize children* as an action.

19. Click on the **From variable** and select the *Children* component variable.

20. Click on the **To variable** and select the *Extra child details* component variable.

21. Click on **Save** to save the form.

**User defined variable**

22. Define a user defined variable that will keep the retrieved data (children). The procedure
    is described here: :ref:`Family members configuration <configuration_prefill_family_members>`.

23. Click on **Save** to save the form.

You can now view the form by clicking on the list **Show form**.
The form consists of two steps, as mentioned above:

**Step 1**: shows the available (retrieved) children

.. image:: _assets/children_prefill_step_1.png


**Step 2**: shows the selected children updated with the *BSN* and the *firstnames* of the
first step, along with the radio field which is the extra information provided manually
by the user 

.. image:: _assets/children_prefill_step_2.png
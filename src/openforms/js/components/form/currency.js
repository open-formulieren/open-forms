import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";
import {DECIMAL_PLACES} from "../form/edit/components"
import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';

import {PREFILL} from './edit/tabs';

CurrencyEditData[0].defaultValue = "EUR";
defineCommonEditFormTabs(Formio.Components.components.currency, CurrencyEditData.concat([DECIMAL_PLACES]));

const origEditForm = Formio.Components.components.currency.editForm;

Formio.Components.components.currency.editForm = function() {
    const form = origEditForm.apply(this);
    form.components[0].components = [
        ...form.components[0].components,
        PREFILL,

    ];

    return form;
}

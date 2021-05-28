import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";
import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';

let decimalPlaces = {
    type: 'number',
    input: true,
    weight: 80,
    key: 'decimalLimit',
    label: 'Decimal Places',
    tooltip: 'The maximum number of decimal places.'
};

defineCommonEditFormTabs(Formio.Components.components.currency, CurrencyEditData.concat([decimalPlaces]));

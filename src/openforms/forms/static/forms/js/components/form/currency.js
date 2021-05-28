import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";
import {DECIMAL_PLACES} from "../form/edit/components"
import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';

defineCommonEditFormTabs(Formio.Components.components.currency, CurrencyEditData.concat([DECIMAL_PLACES]));

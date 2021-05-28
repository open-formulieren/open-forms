import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";
import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';

defineCommonEditFormTabs(Formio.Components.components.currency, CurrencyEditData);

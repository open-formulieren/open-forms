import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";
import {DECIMAL_PLACES} from "../form/edit/components"
import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';

CurrencyEditData[0].defaultValue = "EUR";
defineCommonEditFormTabs(Formio.Components.components.currency, CurrencyEditData.concat([DECIMAL_PLACES]));

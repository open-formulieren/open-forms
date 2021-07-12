import {Formio} from "formiojs";
import {DECIMAL_PLACES} from "../form/edit/components"
import {defineCommonEditFormTabs} from "./abstract";

defineCommonEditFormTabs(Formio.Components.components.number, [DECIMAL_PLACES]);

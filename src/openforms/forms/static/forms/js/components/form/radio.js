import {Formio} from 'formiojs';
import {defineChoicesEditFormTabs} from './abstract';


defineChoicesEditFormTabs(Formio.Components.components.radio);
defineChoicesEditFormTabs(Formio.Components.components.selectboxes);

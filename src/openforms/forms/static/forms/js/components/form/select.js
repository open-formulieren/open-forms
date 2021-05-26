import {Formio} from 'formiojs';
import {defineChoicesEditFormTabs} from './abstract';


defineChoicesEditFormTabs(Formio.Components.components.select, 'data.values');

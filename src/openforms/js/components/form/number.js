import {Formio} from 'formiojs';
import {DECIMAL_PLACES, MAX_VALUE, MIN_VALUE} from './edit/components';
import {defineCommonEditFormTabs} from './abstract';

defineCommonEditFormTabs(Formio.Components.components.number, [DECIMAL_PLACES, MIN_VALUE, MAX_VALUE]);

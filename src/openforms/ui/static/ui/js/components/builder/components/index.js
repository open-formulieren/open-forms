import {Templates} from 'formiojs';
import {component} from './component';
import {field} from './field';
import {label} from './label';
import {message} from './message';
import {text} from './text';
import {multipleMasksInput} from './multiple-masks-input';

const OFLibrary = {
    component: {form: component},
    field: {form: field},
    label: {form: label},
    message: {form: message},

    input: {form: text},
    multipleMasksInput: {form: multipleMasksInput},
};

Templates.current = OFLibrary;

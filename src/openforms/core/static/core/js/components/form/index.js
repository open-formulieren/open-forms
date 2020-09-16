import {Templates} from 'formiojs';
import {component} from './component';
import {field} from './field';
import {label} from './label';
import {message} from './message';
import {button} from './button';
import {text} from './text';
import {multipleMasksInput} from './multiple-masks-input';
import {checkbox} from './checkbox';
import {radio} from './radio';
import {select} from './select';


const OFLibrary = {
    component: {form: component},
    field: {form: field},
    label: {form: label},
    message: {form: message},

    button: {form: button},

    input: {form: text},
    multipleMasksInput: {form: multipleMasksInput},

    checkbox: {form: checkbox},
    radio: {form: radio},

    select: {form: select},
};

Templates.OFLibrary = OFLibrary;
Templates.current = Templates.OFLibrary;

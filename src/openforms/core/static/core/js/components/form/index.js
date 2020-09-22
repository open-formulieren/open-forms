import {Templates} from 'formiojs';
import {button} from './button';
import {checkbox} from './checkbox';
import {columns} from './columns';
import {component} from './component';
import {field} from './field';
import {html} from './html';
import {label} from './label';
import {message} from './message';
import {multipleMasksInput} from './multiple-masks-input';
import {radio} from './radio';
import {select} from './select';
import {survey} from './survey';
import {signature} from './signature';
import {text} from './text';


const OFLibrary = {
    html: {form: html},
    columns: {form: columns},

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

    survey: {form: survey},
    signature: {form: signature},
};

Templates.OFLibrary = OFLibrary;
Templates.current = Templates.OFLibrary;

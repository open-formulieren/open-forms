import builderSidebar from './templates/builderSidebar';
import coSign from './templates/coSign';
import fieldTemplate from './templates/field.ejs';
import columnsTemplate from './templates/columns.ejs';
import componentTemplate from './templates/component.ejs';
import fieldsetTemplate from './templates/fieldset.ejs';
import dmnTemplate from './templates/dmn.ejs';

const TEMPLATES = {
    builderSidebar: {form: builderSidebar},
    coSign: {form: coSign},
    field: {form: fieldTemplate},
    columns: {form: columnsTemplate},
    component: {form: componentTemplate},
    fieldset: {form: fieldsetTemplate},
    dmn: {form: dmnTemplate},
};

export default TEMPLATES;

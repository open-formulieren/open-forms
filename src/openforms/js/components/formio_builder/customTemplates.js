import builderSidebar from './templates/builderSidebar';
import coSign from './templates/coSign';
import fieldTemplate from './templates/field.ejs';
import columnsTemplate from './templates/columns.ejs';

const TEMPLATES = {
    builderSidebar: {form: builderSidebar},
    coSign: {form: coSign},
    field: {form: fieldTemplate},
    columns: {form: columnsTemplate},
};

export default TEMPLATES;

import builderSidebar from './templates/builderSidebar';
import coSign from './templates/coSign';
import fieldTemplate from './templates/field.ejs';

const TEMPLATES = {
    builderSidebar: {form: builderSidebar},
    coSign: {form: coSign},
    field: {form: fieldTemplate},
};

export default TEMPLATES;

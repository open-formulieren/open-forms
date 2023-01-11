import builderSidebar from './templates/builderSidebar';
import coSign from './templates/coSign';
import columnsTemplate from './templates/columns.ejs';
import componentTemplate from './templates/component.ejs';
import fieldTemplate from './templates/field.ejs';
import fieldsetTemplate from './templates/fieldset.ejs';
import translationsDataGrid from './templates/translationsDataGrid';

const TEMPLATES = {
  builderSidebar: {form: builderSidebar},
  coSign: {form: coSign},
  field: {form: fieldTemplate},
  columns: {form: columnsTemplate},
  component: {form: componentTemplate},
  fieldset: {form: fieldsetTemplate},
  translationsDataGrid: {form: translationsDataGrid},
};

export default TEMPLATES;

import addressNL from './templates/addressNL';
import builderSidebar from './templates/builderSidebar';
import children from './templates/children';
import coSign from './templates/coSign';
import columnsTemplate from './templates/columns.ejs';
import componentTemplate from './templates/component.ejs';
import customerProfile from './templates/customerProfile';
import fieldTemplate from './templates/field.ejs';
import fieldsetTemplate from './templates/fieldset.ejs';
import partners from './templates/partners';

const TEMPLATES = {
  builderSidebar: {form: builderSidebar},
  addressNL: {form: addressNL},
  coSign: {form: coSign},
  field: {form: fieldTemplate},
  columns: {form: columnsTemplate},
  component: {form: componentTemplate},
  fieldset: {form: fieldsetTemplate},
  partners: {form: partners},
  children: {form: children},
  customerProfile: {form: customerProfile},
};

export default TEMPLATES;

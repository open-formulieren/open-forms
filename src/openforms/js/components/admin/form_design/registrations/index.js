import {WysiwygWidget} from 'components/admin/RJSFWrapper';

import CamundaOptionsForm from './camunda';
import {onStepEdit} from './handlers';

/**
 * A map of backend ID to components for the (advanced) option forms.
 * @type {Object}
 */
export const BACKEND_OPTIONS_FORMS = {
  camunda: {
    form: CamundaOptionsForm,
    onStepEdit: onStepEdit,
  },
  objects_api: {
    uiSchema: {
      contentJson: {
        'ui:widget': 'textarea',
        'ui:options': {
          rows: 5,
        },
      },
    },
  },
  email: {
    uiSchema: {
      emailContentTemplateText: {
        'ui:widget': 'textarea',
        'ui:options': {
          rows: 5,
        },
      },
      emailContentTemplateHtml: {'ui:widget': WysiwygWidget},
    },
  },
  'zgw-create-zaak': {
    uiSchema: {
      contentJson: {
        'ui:widget': 'textarea',
        'ui:options': {
          rows: 5,
        },
      },
    },
  },
};

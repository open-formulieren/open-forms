import {WysiwygWidget} from 'components/admin/RJSFWrapper';

import CamundaOptionsForm from './camunda';
import {onStepEdit} from './handlers';
import ObjectsApiSummaryHandler from './objectsapi/ObjectsApiSummaryHandler';
import ZGWOptionsForm from './zgw';

/**
 * @typedef {{
 *   form?: React.FC,
 *   uiSchema?: Object,
 *   configurableFromVariables?: boolean | (options: Object) => boolean,
 *   formVariableConfigured: (variableKey: string, options: Object) => boolean,
 *   summaryHandler?: React.FC
 * }} BackendInfo
 * A map of backend ID to components for the (advanced) option forms.
 * @type {{[key: string]: BackendInfo}}
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
      paymentStatusUpdateJson: {
        'ui:widget': 'textarea',
        'ui:options': {
          rows: 5,
        },
      },
    },
    configurableFromVariables: options => options.version === 2,
    formVariableConfigured: (variableKey, options) =>
      options.variablesMapping.some(mapping => mapping.variableKey === variableKey),
    summaryHandler: ObjectsApiSummaryHandler,
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
    form: ZGWOptionsForm,
    // TODO -> update eigenschap mappings
    // onStepEdit: ...,
  },
};

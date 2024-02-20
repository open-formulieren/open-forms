import {WysiwygWidget} from 'components/admin/RJSFWrapper';

import CamundaOptionsForm from './camunda';
import {onCamundaStepEdit, onZGWStepEdit} from './handlers';
import ObjectsApiOptionsForm from './objectsapi/ObjectsApiOptionsForm';
import ObjectsApiSummaryHandler from './objectsapi/ObjectsApiSummaryHandler';
import ObjectsApiVariableConfigurationEditor from './objectsapi/ObjectsApiVariableConfigurationEditor';
import ZGWOptionsForm from './zgw';

/**
 * @typedef {{
 *   form?: React.FC,
 *   uiSchema?: Object,
 *   configurableFromVariables?: boolean | (options: Object) => boolean,
 *   formVariableConfigured: (variable: Object, options: Object) => boolean,
 *   summaryHandler?: React.FC
 * }} BackendInfo
 * A map of backend ID to components for the (advanced) option forms.
 * @type {{[key: string]: BackendInfo}}
 */
export const BACKEND_OPTIONS_FORMS = {
  camunda: {
    form: CamundaOptionsForm,
    onStepEdit: onCamundaStepEdit,
  },
  objects_api: {
    form: ObjectsApiOptionsForm,
    onStepEdit: null,
    configurableFromVariables: options => options.version === 2,
    formVariableConfigured: (variable, options) =>
      options.variablesMapping.some(mapping => mapping.variableKey === variable.key),
    summaryHandler: ObjectsApiSummaryHandler,
    variableConfigurationEditor: ObjectsApiVariableConfigurationEditor,
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
    onStepEdit: onZGWStepEdit,
  },
};

import {WysiwygWidget} from 'components/admin/RJSFWrapper';

import CamundaOptionsForm from './camunda';
import ObjectsApiOptionsForm from './objectsapi/ObjectsApiOptionsForm';
import ObjectsApiSummaryHandler from './objectsapi/ObjectsApiSummaryHandler';
import ObjectsApiVariableConfigurationEditor from './objectsapi/ObjectsApiVariableConfigurationEditor';
import {onCamundaStepEdit, onObjectsAPIStepEdit, onZGWStepEdit} from './stepEditHandlers';
import {onObjectsAPIUserDefinedVariableEdit} from './userDefinedVariableEditHandlers';
import ZGWOptionsForm from './zgw';

/**
 * @typedef {{
 *   form?: React.FC,
 *   uiSchema?: Object,
 *   onStepEdit?: (...args: any) => Object | null,
 *   onUserDefinedVariableEdit?: (...args: any) => Object | null,
 *   configurableFromVariables?: boolean | (options: Object) => boolean,
 *   summaryHandler?: React.FC
 *   variableConfigurationEditor?: React.FC
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
    onStepEdit: onObjectsAPIStepEdit,
    onUserDefinedVariableEdit: onObjectsAPIUserDefinedVariableEdit,
    configurableFromVariables: options => options.version === 2,
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
  'stuf-zds-create-zaak:ext-utrecht': {
    uiSchema: {
      paymentStatusUpdateMapping: {
        'ui:orderable': false,
        items: {
          'ui:orderable': false,
          'ui:removable': false,
        },
      },
    },
  },
};

import DemoOptionsForm from './demo';
import EmailOptionsForm from './email';
import {
  GenericJSONOptionsForm,
  GenericJSONSummaryHandler,
  GenericJSONVariableConfigurationEditor,
} from './generic_json';
import MSGraphOptionsForm from './ms_graph';
import ObjectsApiOptionsForm from './objectsapi/ObjectsApiOptionsForm';
import ObjectsApiSummaryHandler from './objectsapi/ObjectsApiSummaryHandler';
import {ObjectsApiVariableConfigurationEditor} from './objectsapi/ObjectsApiVariableConfigurationEditor';
import {
  formikValuesToOptions as objectsFormikValuesToOptions,
  optionsToFormikValues as objectsOptionsToFormikValues,
} from './objectsapi/transformations';
import {onGenericJSONStepEdit, onObjectsAPIStepEdit, onZGWStepEdit} from './stepEditHandlers';
import StufZDSOptionsForm from './stufzds';
import {
  onGenericJSONUserDefinedVariableEdit,
  onObjectsAPIUserDefinedVariableEdit,
} from './userDefinedVariableEditHandlers';
import ZGWOptionsForm from './zgw';
import ZGWSummaryHandler from './zgw/SummaryHandler';
import ZGWVariableConfigurationEditor from './zgw/VariableConfigurationEditor';
import {
  formikValuesToOptions as ZGWFormikValuesToOptions,
  optionsToFormikValues as ZGWOptionsToFormikValues,
} from './zgw/transformations';

/**
 * @typedef {{
 *   form: React.FC,
 *   onStepEdit?: (...args: any) => Object | null,
 *   onUserDefinedVariableEdit?: (...args: any) => Object | null,
 *   configurableFromVariables?: boolean | (variable: Object, component: Object | undefined, options: Object) => boolean,
 *   summaryHandler?: React.FC
 *   variableConfigurationEditor?: React.FC
 * }} BackendInfo
 * A map of backend ID to components for the (advanced) option forms.
 * @type {{[key: string]: BackendInfo}}
 */
export const BACKEND_OPTIONS_FORMS = {
  objects_api: {
    form: ObjectsApiOptionsForm,
    onStepEdit: onObjectsAPIStepEdit,
    onUserDefinedVariableEdit: onObjectsAPIUserDefinedVariableEdit,
    configurableFromVariables: (variable, component, options) =>
      options.version === 2 || (component && component.type === 'file'),
    summaryHandler: ObjectsApiSummaryHandler,
    variableConfigurationEditor: ObjectsApiVariableConfigurationEditor,
    optionsToFormikValues: objectsOptionsToFormikValues,
    formikValuesToOptions: objectsFormikValuesToOptions,
  },
  email: {
    form: EmailOptionsForm,
  },
  'zgw-create-zaak': {
    form: ZGWOptionsForm,
    onStepEdit: onZGWStepEdit,
    configurableFromVariables: (variable, component, options) =>
      component && component.type === 'file',
    summaryHandler: ZGWSummaryHandler,
    variableConfigurationEditor: ZGWVariableConfigurationEditor,
    optionsToFormikValues: ZGWOptionsToFormikValues,
    formikValuesToOptions: ZGWFormikValuesToOptions,
  },
  'stuf-zds-create-zaak': {
    form: StufZDSOptionsForm,
  },
  'microsoft-graph': {form: MSGraphOptionsForm},
  json_dump: {
    form: GenericJSONOptionsForm,
    configurableFromVariables: true,
    summaryHandler: GenericJSONSummaryHandler,
    variableConfigurationEditor: GenericJSONVariableConfigurationEditor,
    onStepEdit: onGenericJSONStepEdit,
    onUserDefinedVariableEdit: onGenericJSONUserDefinedVariableEdit,
  },
  // demo plugins
  demo: {form: DemoOptionsForm},
  'failing-demo': {form: DemoOptionsForm},
  'exception-demo': {form: DemoOptionsForm},
};

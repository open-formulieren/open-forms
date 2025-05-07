import CamundaOptionsForm from './camunda';
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
  onCamundaStepEdit,
  onGenericJSONStepEdit,
  onObjectsAPIStepEdit,
  onZGWStepEdit,
} from './stepEditHandlers';
import StufZDSOptionsForm from './stufzds';
import {
  onGenericJSONUserDefinedVariableEdit,
  onObjectsAPIUserDefinedVariableEdit,
} from './userDefinedVariableEditHandlers';
import ZGWOptionsForm from './zgw';

/**
 * @typedef {{
 *   form: React.FC,
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
    form: EmailOptionsForm,
  },
  'zgw-create-zaak': {
    form: ZGWOptionsForm,
    onStepEdit: onZGWStepEdit,
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

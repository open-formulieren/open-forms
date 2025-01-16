import CamundaOptionsForm from './camunda';
import DemoOptionsForm from './demo';
import EmailOptionsForm from './email';
import {
  JSONDumpOptionsForm,
  JSONDumpSummaryHandler,
  JSONDumpVariableConfigurationEditor,
} from './json_dump';
import MSGraphOptionsForm from './ms_graph';
import ObjectsApiOptionsForm from './objectsapi/ObjectsApiOptionsForm';
import ObjectsApiSummaryHandler from './objectsapi/ObjectsApiSummaryHandler';
import {ObjectsApiVariableConfigurationEditor} from './objectsapi/ObjectsApiVariableConfigurationEditor';
import {onCamundaStepEdit, onObjectsAPIStepEdit, onZGWStepEdit} from './stepEditHandlers';
import StufZDSOptionsForm from './stufzds';
import {onObjectsAPIUserDefinedVariableEdit} from './userDefinedVariableEditHandlers';
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
    form: JSONDumpOptionsForm,
    configurableFromVariables: true,
    summaryHandler: JSONDumpSummaryHandler,
    variableConfigurationEditor: JSONDumpVariableConfigurationEditor,
  },
  // demo plugins
  demo: {form: DemoOptionsForm},
  'failing-demo': {form: DemoOptionsForm},
  'exception-demo': {form: DemoOptionsForm},
};

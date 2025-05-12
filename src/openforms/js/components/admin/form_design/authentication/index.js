import DigidOptionsForm from './digid/DigidOptionsForm';
import YiviOptionsForm from './yivi/YiviOptionsForm';

/**
 * @typedef {{
 *   form: React.FC,
 * }} BackendInfo
 * A map of backend ID to components for the option forms.
 * @type {{[key: string]: BackendInfo}}
 */
export const BACKEND_OPTIONS_FORMS = {
  digid: {
    form: DigidOptionsForm,
  },
  yivi_oidc: {
    form: YiviOptionsForm,
  },
};

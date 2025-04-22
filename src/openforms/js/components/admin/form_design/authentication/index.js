import DigidOptionsForm from './digid/DigidOptionsForm';

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
};

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
};

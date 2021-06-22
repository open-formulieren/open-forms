import {Formio} from 'formiojs';

import DEFAULT_TABS from './edit/tabs';

const Time = Formio.Components.components.time;

/**
 * Time 24h format is functional by not using the HTML5 widget, but rather the mask
 * input & specify the moment format to use. This still runs the validation and allows
 * us to enter times in 24h notation.
 */
class TimeField extends Time {
    static schema(...extend) {
        return Time.schema({
            inputType: 'text',
            format: 'HH:mm',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Time',
            icon: 'clock-o',
            group: 'basic',
            weight: 10,
            schema: TimeField.schema(),
        };
    }

    static editForm() {
        return {components: [DEFAULT_TABS]};
    }

    get defaultSchema() {
        return TimeField.schema();
    }
}

export default TimeField;

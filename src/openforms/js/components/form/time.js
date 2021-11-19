import {Formio} from 'formiojs';

import DEFAULT_TABS, {ADVANCED, REGISTRATION, SENSITIVE_BASIC, VALIDATION} from './edit/tabs';

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
            minTime: null,
            maxTime: null,
            validateOn: 'blur'
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
        const extra = [
            {
                type: 'time',
                input: true,
                key: 'minTime',
                label: 'Minimum Time',
                weight: 10,
                tooltip: 'The minimum time that can be picked.',
            },
            {
                type: 'time',
                input: true,
                key: 'maxTime',
                label: 'Maximum Time',
                weight: 10,
                tooltip: 'The maximum time that can be picked.',
            },
        ];

        const BASIC_TAB = {
            ...SENSITIVE_BASIC,
            components: [
                ...SENSITIVE_BASIC.components,
                ...extra,
            ]
        };
        const TABS = {
            ...DEFAULT_TABS,
            components: [
                BASIC_TAB,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
            ]
        };
        return {components: [TABS]};
    }

    get defaultSchema() {
        return TimeField.schema();
    }
}

export default TimeField;

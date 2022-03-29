import {ADVANCED, PREFILL, REGISTRATION, SENSITIVE_BASIC, VALIDATION} from './edit/tabs';
import TextField from './textfield';
import {READ_ONLY} from './edit/options';


class BsnField extends TextField {
    static schema(...extend) {
        return TextField.schema({
            type: 'bsn',
            label: 'BSN',
            key: 'bsn',
            inputMask: '999999999',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'BSN Field',
            icon: 'id-card-o',
            group: 'basic',
            weight: 10,
            schema: BsnField.schema(),
        };
    }

    static editForm() {
        const updatedSensitiveBasicTab = {
            ...SENSITIVE_BASIC,
            components: [
                ...SENSITIVE_BASIC.components,
                READ_ONLY
            ]
        };

        const tabs = {
            type: 'tabs',
            key: 'tabs',
            components: [
                updatedSensitiveBasicTab,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
                PREFILL,
            ]
        };
        return {components: [tabs]};
    }

    get defaultSchema() {
        return BsnField.schema();
    }

}

export default BsnField;

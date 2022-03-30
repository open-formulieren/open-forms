import {ADVANCED, PREFILL, REGISTRATION, SENSITIVE_READ_ONLY, VALIDATION} from './edit/tabs';
import TextField from './textfield';


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
        const tabs = {
            type: 'tabs',
            key: 'tabs',
            components: [
                SENSITIVE_READ_ONLY,
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

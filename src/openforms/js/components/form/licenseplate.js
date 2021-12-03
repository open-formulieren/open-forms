import {Formio} from 'formiojs';
import {DEFAULT_SENSITIVE_TABS} from './edit/tabs';

const TextField = Formio.Components.components.textfield;


class LicensePlate extends TextField {
    static schema(...extend) {
        return TextField.schema({
            type: 'licenseplate',
            label: 'License plate',
            key: 'licenseplate',
            validateOn: 'blur',
            validate: {
                pattern: '^[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}$'
            },
            errors: {
                pattern: 'Invalid Dutch license plate'
            },
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'License plate',
            icon: 'car',
            group: 'basic',
            weight: 10,
            schema: LicensePlate.schema(),
        };
    }

    static editForm() {
        return {components: [DEFAULT_SENSITIVE_TABS]};
    }

    get defaultSchema() {
        return LicensePlate.schema();
    }

}

export default LicensePlate;

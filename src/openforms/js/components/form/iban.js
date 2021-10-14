import {Formio} from "formiojs";
import {DEFAULT_SENSITIVE_TABS} from "./edit/tabs";

const TextField = Formio.Components.components.textfield;


class IbanField extends TextField {
    static schema(...extend) {
        return TextField.schema({
            type: 'iban',
            label: 'IBAN',
            key: 'iban',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'IBAN Field',
            icon: 'wallet',
            group: 'basic',
            weight: 10,
            schema: IbanField.schema(),
        };
    }

    static editForm() {
        return {components: [DEFAULT_SENSITIVE_TABS]};
    }

    get defaultSchema() {
        return IbanField.schema();
    }

}

export default IbanField;

import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const TextField = Formio.Components.components.textfield;


class IbanField extends TextField {
    static schema(...extend) {
        return TextField.schema({
            type: 'iban',
            label: 'IBAN',
            key: 'iban',
            validate: {
                custom: true,
            }
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'IBAN Field',
            icon: 'fa fa-wallet',
            group: 'basic',
            weight: 10,
            schema: IbanField.schema(),
        };
    }

    get defaultSchema() {
        return IbanField.schema();
    }

}

defineCommonEditFormTabs(IbanField);

export default IbanField;

import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const PhoneNumber = Formio.Components.components.phoneNumber;


class PhoneNumberField extends PhoneNumber {
    static schema(...extend) {
        return PhoneNumber.schema({
            inputMask: null,
            validate: {
                custom: true,
            }
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Phone Number Field',
            icon: 'phone-square',
            group: 'basic',
            weight: 10,
            schema: PhoneNumberField.schema(),
        };
    }

    get defaultSchema() {
        return PhoneNumberField.schema();
    }

}

defineCommonEditFormTabs(PhoneNumberField);

export default PhoneNumberField;

import {Formio} from "formiojs";
import DEFAULT_TABS from "./edit/tabs";

const PhoneNumber = Formio.Components.components.phoneNumber;


class PhoneNumberField extends PhoneNumber {

    static schema(...extend) {
        return PhoneNumber.schema({
            inputMask: null
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

    static editForm() {
        return {components: [DEFAULT_TABS]};
    }

    get defaultSchema() {
        return PhoneNumberField.schema();
    }

}

export default PhoneNumberField;

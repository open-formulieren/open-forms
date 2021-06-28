import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const PhoneNumber = Formio.Components.components.phoneNumber;


class PhoneNumberField extends PhoneNumber {

    handleInput(value) {
        value = value.replace(/[^0-9 -+]/gi,'');
        console.log(`In handleInput, returning ${value}`);
        return value;
    }

    addFocusBlurEvents(element) {
        super.addFocusBlurEvents(element);

        this.addEventListener(element, 'keyup', () => {
            console.log(`In element keyup, got value ${element.value}`);
            element.value = this.handleInput(element.value);
        });
      }

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

    get defaultSchema() {
        return PhoneNumberField.schema();
    }

}

defineCommonEditFormTabs(PhoneNumberField);

export default PhoneNumberField;

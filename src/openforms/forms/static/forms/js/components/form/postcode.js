import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const TextField = Formio.Components.components.textfield;


class PostcodeField extends TextField {
    static schema(...extend) {
        return TextField.schema({
            type: 'postcode',
            label: 'Postcode',
            key: 'postcode',
            inputMask: '9999 AA',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Postcode Field',
            icon: 'home',
            group: 'basic',
            weight: 10,
            schema: PostcodeField.schema(),
        };
    }

    get defaultSchema() {
        return PostcodeField.schema();
    }

}

defineCommonEditFormTabs(PostcodeField);

export default PostcodeField;

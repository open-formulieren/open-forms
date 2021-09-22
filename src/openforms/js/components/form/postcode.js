import {DEFAULT_SENSITIVE_TABS, PREFILL} from './edit/tabs';
import TextField from './textfield';


class PostcodeField extends TextField {
    static schema(...extend) {
        return TextField.schema({
            type: 'postcode',
            label: 'Postcode',
            key: 'postcode',
            inputMask: '9999 AA',
            validateOn: 'blur',
            validate: {
              customMessage: 'Invalid Postcode'
            }
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

    static editForm() {
        const tabs = {
            ...DEFAULT_SENSITIVE_TABS,
            components: [
                ...DEFAULT_SENSITIVE_TABS.components,
                PREFILL,
            ],
        };
        return {components: [tabs]};
    }

    get defaultSchema() {
        return PostcodeField.schema();
    }
}

export default PostcodeField;

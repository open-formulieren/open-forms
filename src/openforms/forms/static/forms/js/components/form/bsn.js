import {Formio} from "formiojs";
import DEFAULT_TABS from "./edit/tabs";

const TextField = Formio.Components.components.textfield;


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
            icon: 'hashtag',
            group: 'basic',
            weight: 10,
            schema: BsnField.schema(),
        };
    }

    static editForm() {
        return {components: [DEFAULT_TABS]};
    }

    get defaultSchema() {
        return BsnField.schema();
    }

}

export default BsnField;

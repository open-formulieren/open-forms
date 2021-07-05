import {Formio} from "formiojs";

import DEFAULT_TABS from "./edit/tabs";
import TextField from './text';


class BsnField extends TextField {
    static schema(...extend) {
        return TextField.schema({
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

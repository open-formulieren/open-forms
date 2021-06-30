import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const NumberField = Formio.Components.components.number;


class BsnField extends NumberField {
    static schema(...extend) {
        return NumberField.schema({
            type: 'bsn',
            label: 'BSN',
            key: 'bsn',
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

    get defaultSchema() {
        return BsnField.schema();
    }

}

defineCommonEditFormTabs(BsnField);

export default BsnField;

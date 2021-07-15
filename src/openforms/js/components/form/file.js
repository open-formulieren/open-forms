import {Formio} from "formiojs";
import {DEFAULT_FILE_TABS} from "./edit/tabs";

const BaseFileField = Formio.Components.components.file;


class FileField extends BaseFileField {
    static schema(...extend) {
        return BaseFileField.schema({
            type: 'file',
            label: 'File Upload',
            key: 'file',
            storage: "url",
            // TODO this needs to be passed in
            url: "http://localhost:8000/api/v1/submissions/files/upload",
            webcam: false,
            input: true,
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'File Upload',
            icon: 'file',
            group: 'basic',
            weight: 10,
            schema: FileField.schema(),
        };
    }

    get defaultSchema() {
        return FileField.schema();
    }

    static editForm() {
        return {components: [DEFAULT_FILE_TABS]};
    }
}


export default FileField;

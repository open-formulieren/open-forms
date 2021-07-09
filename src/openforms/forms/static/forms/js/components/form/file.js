import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const BaseFileField = Formio.Components.components.file;


class FileField extends BaseFileField {
    static schema(...extend) {
        return BaseFileField.schema({
            type: 'file',
            label: 'File Upload',
            key: 'file',
            storage: "url",
            url: "http://localhost:8000/api/v1/submissions/files/upload",
            webcam: false,
            input: true,
            fileTypes: [
                {
                    "label": "",
                    "value": ""
                }
                // {
                //     "label": "PDF",
                //     "value": ".pdf"
                // },
                // {
                //     "label": "PNG",
                //     "value": ".png"
                // }
            ],
            // TODO read backend size limits to from this configuration
            "fileMinSize": "10KB",
            "fileMaxSize": "2GB",
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

}

defineCommonEditFormTabs(FileField);

export default FileField;

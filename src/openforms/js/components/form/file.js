import {Formio} from 'formiojs';
import {ADVANCED, BASIC} from './edit/tabs';
import {getFullyQualifiedUrl} from '../../utils/urls';

const BaseFileField = Formio.Components.components.file;


// https://github.com/open-formulieren/open-forms/issues/223

// pdf xls vlsx (xlsx?) csv doc dockx (docx?) jpg png, zip, rar, tar en alle open office formaten

const MIME_TYPE_FILTERS = {
    "All": "*",
    ".png": "image/png",
    ".jpg": "image/jpeg",

    ".pdf": "application/pdf",

    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",

    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

    "Open Office": ["application/vnd.oasis.opendocument.*",
        "application/vnd.stardivision.*",
        "application/vnd.sun.xml.*"].join(","),

    ".zip": "application/zip",
    ".rar": "application/vnd.rar",
    ".tar": "application/x-tar",
    // if we want .tar you'd expect .gz
    // ".gz": "application/gzip",
}


function as_choices(obj) {
    return Object.keys(obj).map(key => {
        return {"label": key, "value": obj[key]};
    })
}

const FILE_TAB = {
    key: 'file',
    label: 'File',
    components: [
        // {
        //     type: 'textfield',
        //     input: true,
        //     key: 'fileNameTemplate',
        //     label: 'File Name Template',
        //     placeholder: '(optional) {name}-{guid}',
        //     tooltip: 'Specify template for name of uploaded file(s). Regular template variables are available (`data`, `component`, `user`, `value`, `moment` etc.), also `fileName`, `guid` variables are available. `guid` part must be present, if not found in template, will be added at the end.',
        //     weight: 25
        // },
        {
            type: 'textfield',
            input: true,
            key: 'file.name',
            label: 'File Name',
            placeholder: '(optional)',
            tooltip: 'Specify template for name of uploaded file(s).',
            weight: 25
        },
        {
            type: 'select',
            key: 'file.type',
            input: true,
            label: 'Select',
            widget: 'choicesjs',
            tableView: true,
            multiple: true,
            data: {
                values: as_choices(MIME_TYPE_FILTERS),
            },
            weight: 30
        },
        {
            type: 'checkbox',
            input: true,
            key: 'image.resize.apply',
            label: 'Resize image',
            tooltip: 'When this is checked, the image will be resized.',
            weight: 33,
            customConditional: 'show = data.file.type.some(function(v) { return (v.indexOf("image/") > -1) || (v == "*"); });',
        },
        {
            key: 'image.resize.columns',
            type: 'columns',
            input: false,
            tableView: false,
            label: 'Columns',
            columns: [
                {
                    components: [
                        {
                            key: 'image.resize.width',
                            type: 'number',
                            label: 'Maximum width',
                            mask: false,
                            tableView: false,
                            delimiter: false,
                            requireDecimal: false,
                            inputFormat: 'plain',
                            truncateMultipleSpaces: false,
                            input: true,
                            defaultValue: 2000
                        }
                    ],
                    width: 6,
                    offset: 0,
                    push: 0,
                    pull: 0,
                    size: 'md',
                    currentWidth: 6
                },
                {
                    components: [
                        {
                            key: 'image.resize.height',
                            type: 'number',
                            label: 'Maximum height',
                            mask: false,
                            tableView: false,
                            delimiter: false,
                            requireDecimal: false,
                            inputFormat: 'plain',
                            truncateMultipleSpaces: false,
                            input: true ,
                            defaultValue: 2000
                        }
                    ],
                    width: 6,
                    offset: 0,
                    push: 0,
                    pull: 0,
                    size: 'md',
                    currentWidth: 6
                }
            ],
            conditional: {
                json: {'==': [{var: 'data.image.resize.apply'}, true]}
            }
        },
        {
            // used by the formio widget
            type: 'hidden',
            input: false,
            key: 'filePattern',
            label: 'File Pattern',
            logic: [
                {
                    name: 'filePatternTrigger',
                    trigger: {
                        type: 'javascript',
                        javascript: 'result = true;'
                    },
                    actions: [
                        {
                            name: 'filePatternAction',
                            type: 'customAction',
                            customAction: 'value = data.file.type.join(",")'
                        }
                    ]
                }
            ],
            weight: 50
        },
        {
            // used by the formio widget
            type: 'textfield',
            input: true,
            key: 'fileMaxSize',
            label: 'File Maximum Size',
            placeholder: '10MB',
            tooltip: 'See <a href=\'https://github.com/danialfarid/ng-file-upload#full-reference\' target=\'_blank\'>https://github.com/danialfarid/ng-file-upload#full-reference</a> for how to specify file sizes.',
            weight: 70
        },
        // {
        //     // used by the formio widget
        //     type: 'checkbox',
        //     input: true,
        //     key: 'webcam',
        //     label: 'Enable web camera',
        //     tooltip: 'This will allow using an attached camera to directly take a picture instead of uploading an existing file.',
        //     weight: 32,
        //     conditional: {
        //         json: {'==': [{var: 'data.file.type'}, 'image']}
        //     }
        // },
    ],
};

class FileField extends BaseFileField {
    static schema(...extend) {
        return BaseFileField.schema({
            type: 'file',
            label: 'File Upload',
            key: 'file',
            storage: 'url',
            url: getFullyQualifiedUrl('/api/v1/submissions/files/upload'),
            options: "{\"withCredentials\": true}",
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
        return {components: [{
            type: 'tabs',
            key: 'file',
            components: [
                BASIC,
                ADVANCED,
                FILE_TAB,
            ]
        }]};
    }
}


export default FileField;

import {BuilderUtils, Utils} from 'formiojs';

export const defineInputInfo = (ComponentClass, className, inputType = '', widgetType = '', contentPath = '') => {
    Object.defineProperty(ComponentClass.prototype, 'inputInfo', {
            get: function () {
                const componentClass = new ComponentClass();
                componentClass.component = this.component;
                const info = componentClass.elementInfo();

                // Set class name.
                info.attr.class = className;

                // Allow specifying input type.
                if (inputType) {
                    info.type = inputType;
                }

                // Allow targeting content by dot (.) separated path.
                if (contentPath) {
                    let content = this;
                    const parts = contentPath.split('.');

                    parts.forEach(part => {
                        content = content[part];
                    });

                    info.content = this.t(this.component.label);
                }

                // Copy schema attrs.
                Object.entries(this.schema).forEach(([k, v]) => {
                    if (info.attr.hasOwnProperty(k)) {
                        info.attr[k] = v;
                    }
                });

                // Merge results.
                const result = {};
                Object.assign(result, this.schema);
                Object.assign(result, this.component);
                Object.assign(result, info);

                result.component.widget = 'html5';

                return result;
            }
        }
    );
}


export const defineEditFormTabs = (ComponentClass, tabs) => {
    ComponentClass.editForm = function () {
        return {
            components: tabs
        };
    };
};

export const defineCommonEditFormTabs = (ComponentClass, extra = []) => {
    defineEditFormTabs(ComponentClass, [
        {
            type: 'tabs', key: 'tabs', components: [
                {
                    key: 'basic',
                    label: 'Basic',
                    components: [
                        {
                            type: 'textfield', key: 'label', label: 'Label'
                        },
                        {
                            type: 'textfield', key: 'key', label: 'Property Name'
                        },
                        {
                            type: 'textfield', key: 'description', label: 'Description'
                        },
                        ...extra,
                    ]
                },
                {
                    key: 'advanced',
                    label: 'Advanced',
                    components: [
                        {
                            type: 'panel',
                            title: 'Simple',
                            key: 'simple-conditional',
                            theme: 'default',
                            components: [
                                {
                                    type: 'select',
                                    input: true,
                                    label: 'This component should Display:',
                                    key: 'conditional.show',
                                    dataSrc: 'values',
                                    data: {
                                        values: [
                                            {label: 'True', value: 'true'},
                                            {label: 'False', value: 'false'}
                                        ]
                                    }
                                },
                                {
                                    type: 'select',
                                    input: true,
                                    label: 'When the form component:',
                                    key: 'conditional.when',
                                    dataSrc: 'custom',
                                    valueProperty: 'value',
                                    data: {
                                        custom(context) {
                                            return Utils.getContextComponents(context);
                                        }
                                    }
                                },
                                {
                                    type: 'textfield',
                                    input: true,
                                    label: 'Has the value:',
                                    key: 'conditional.eq'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]);
};


export const defineChoicesEditFormTabs = (ComponentClass, valueKey = 'values') => {
    defineCommonEditFormTabs(ComponentClass, [{
            type: 'datagrid',
            input: true,
            label: 'Values',
            key: valueKey,
            tooltip: 'The radio button values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
            weight: 10,
            reorder: true,
            defaultValue: [{label: '', value: ''}],
            components: [
                {
                    label: 'Label',
                    key: 'label',
                    input: true,
                    type: 'textfield',
                },
                {
                    label: 'Value',
                    key: 'value',
                    input: true,
                    type: 'textfield',
                    allowCalculateOverride: true,
                    calculateValue: {_camelCase: [{var: 'row.label'}]},
                    validate: {
                        required: true
                    }
                },
            ],
        }]
    );
};

import {Formio} from 'react-formio';

import {getFullyQualifiedUrl} from '../../utils/urls';

const FieldComponent = Formio.Components.components.field;

// TODO: in the future, allow selection of an auth plugin (from the registry)
const EDIT_FORM_TABS = [
    {
        type: 'tabs',
        key: 'tabs',
        components: [
            {
                key: 'basic',
                label: 'Basic',
                components: [
                    {
                        type: 'textfield',
                        key: 'label',
                        label: 'Label'
                    },
                    {
                        type: 'textfield',
                        key: 'description',
                        label: 'Description'
                    },
                    {
                        type: 'select',
                        key: 'authPlugin',
                        label: 'Authentication method',
                        description: `
                            Which authentication method the co-signer must use. Note that this must be an
                            authentication method available on the form.`,
                        dataSrc: 'url',
                        data: {
                            // if the url starts with '/', then formio will prefix it with the formio
                            // base URL, which is of course wrong. We there explicitly use the detected
                            // host.
                            url: getFullyQualifiedUrl('/api/v1/authentication/plugins'),
                        },
                        valueProperty: 'id',
                        template: `<span>{{ item.label }}, provides: {{ item.providesAuth.join(', ') }}</span>`,
                    }
                ],
            }
        ]
    }
];


/**
 * A component for co-signing a form.
 *
 * Co-signing is achieved through a second authentication on the form with a slightly
 * different path. The component probes the submission state to check whether it's
 * co-signed or not, and if it's not, a login-button from the configured plugin is
 * presented.
 */
class CoSignField extends FieldComponent {

    constructor(component, options, data) {
        super(component, options, data);
        this.checks = [];
    }

    static schema(...extend) {
        return FieldComponent.schema({
            label: 'Co-sign',
            type: 'coSign',
            authPlugin: 'digid',
            input: false,
        }, ...extend);
    }

    static get builderInfo() {
      return {
        title: 'Co-sign',
        icon: 'id-card-o',
        group: 'basic',
        weight: 300,
        schema: CoSignField.schema()
      };
    }

    static editForm() {
        return {components: EDIT_FORM_TABS};
    }

    render(content) {
        const btnContent = this.t(
            'Co-Sign ({{ authPlugin }})',
            {authPlugin: this.component.authPlugin}
        );
        const context = {
            content: content,
            btnContent: btnContent,
        };
        return super.render(this.renderTemplate('coSign', context));
    }

}


export default CoSignField;

import {Formio} from 'react-formio';

import {AUTH_PLUGINS_ENDPOINT} from 'components/admin/form_design/constants.js';
import {DESCRIPTION, HIDDEN, LABEL_REQUIRED} from 'components/form/edit/options';
import {getFullyQualifiedUrl} from 'utils/urls';

import {TRANSLATIONS} from './edit/tabs';
import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

export const COSIGN_OLD_TYPE_KEY = 'coSign';

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
          LABEL_REQUIRED,
          DESCRIPTION,
          {
            type: 'select',
            key: 'authPlugin',
            label: 'Authentication method',
            description:
              'Which authentication method the co-signer must use. Note that this must be an authentication method available on the form.',
            dataSrc: 'url',
            data: {
              // if the url starts with '/', then formio will prefix it with the formio
              // base URL, which is of course wrong. So, we explicitly use the detected
              // host.
              url: getFullyQualifiedUrl(AUTH_PLUGINS_ENDPOINT),
            },
            valueProperty: 'id',
            template: `<span>{{ item.label }}, provides: {{ item.providesAuth }}</span>`,
          },
          HIDDEN,
        ],
      },
      TRANSLATIONS,
    ],
  },
];

/**
 * A component for co-signing a form.
 *
 * Co-signing is achieved through a second authentication on the form with a slightly
 * different path. The component probes the submission state to check whether it's
 * co-signed or not, and if it's not, a login-button from the configured plugin is
 * presented.
 */
class CoSignFieldOld extends FieldComponent {
  constructor(component, options, data) {
    super(component, options, data);
    this.checks = [];
  }

  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'Co-sign',
        type: COSIGN_OLD_TYPE_KEY,
        authPlugin: 'digid',
        input: false,
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Co-sign (Old)',
      icon: 'id-card-o',
      group: 'basic',
      weight: 300,
      schema: CoSignFieldOld.schema(),
    };
  }

  static editForm() {
    return {components: EDIT_FORM_TABS};
  }

  render(content) {
    const btnContent = this.t('Co-Sign ({{ authPlugin }})', {
      authPlugin: this.component.authPlugin,
    });
    const context = {
      content: content,
      btnContent: btnContent,
    };
    return super.render(this.renderTemplate('coSign', context));
  }
}

export default CoSignFieldOld;

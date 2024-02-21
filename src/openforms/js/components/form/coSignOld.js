import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

export const COSIGN_V1_TYPE = 'coSign';

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
        type: COSIGN_V1_TYPE,
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

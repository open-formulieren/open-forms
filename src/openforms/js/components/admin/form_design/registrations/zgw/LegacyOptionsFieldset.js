import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';

import {LegacyCaseType, LegacyDocumentType} from './fields';

/**
 * @deprecated
 */
const LegacyOptionsFieldset = () => (
  <Fieldset
    title={
      <FormattedMessage
        description="ZGw APIs registration: legacy configuration options fieldset title"
        defaultMessage="Legacy configuration"
      />
    }
    fieldNames={['zaaktype', 'informatieobjecttype']}
    collapsible
  >
    <div className="description">
      <FormattedMessage
        description="ZGW APIs legacy config options informative message"
        defaultMessage={`The configuration options here are legacy options. They
          will continue working, but you should upgrade to the new configuration
          options above. If a new configuration option is specified, the matching
          legacy option will be ignored.`}
      />
    </div>
    <LegacyCaseType />
    <LegacyDocumentType />
  </Fieldset>
);

export default LegacyOptionsFieldset;

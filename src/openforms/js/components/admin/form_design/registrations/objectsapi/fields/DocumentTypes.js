import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';

import CatalogueSelect from './CatalogueSelect';

export const DocumentTypesFieldet = () => (
  <Fieldset
    title={
      <FormattedMessage
        description="Objects registration: document types"
        defaultMessage="Document types"
      />
    }
    collapsible
    fieldNames={['catalogue']}
  >
    <div className="description">
      <FormattedMessage
        description="New document types informative message"
        defaultMessage={`The legacy document types configuration will be ignored
        as soon as a catalogue is selected, even if you don't select any document
        type in the dropdowns.`}
      />
    </div>
    <CatalogueSelect />
  </Fieldset>
);

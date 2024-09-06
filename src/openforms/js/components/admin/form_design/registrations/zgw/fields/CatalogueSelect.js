import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import {CatalogueSelect as GenericCatalogueSelect} from 'components/admin/forms/zgw';

const CatalogueSelect = ({loading, optionGroups}) => {
  const {values: zgwApiGroup = null} = useFormikContext();
  // TODO: make required when case type can be selected in a dropdown AND there is no
  // legacy case type or document type URL specified. Probably best to do this as
  // backend validation so that new registration backends must select a catalogue.
  // TODO: ensure that case_type_identification is reset when the group is changed
  return (
    <GenericCatalogueSelect
      label={
        <FormattedMessage
          description="ZGW APIs registration options 'catalogue' label"
          defaultMessage="Catalogue"
        />
      }
      isDisabled={!zgwApiGroup}
      loading={loading}
      optionGroups={optionGroups}
    />
  );
};

CatalogueSelect.propTypes = {
  loading: PropTypes.bool.isRequired,
  optionGroups: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      options: PropTypes.arrayOf(
        PropTypes.shape({
          rsin: PropTypes.string.isRequired,
          domain: PropTypes.string.isRequired,
          label: PropTypes.string.isRequired,
        })
      ).isRequired,
    })
  ),
};

export default CatalogueSelect;

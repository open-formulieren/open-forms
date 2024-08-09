import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

export const extractValue = (optionGroups, currentValue) => {
  const allOptions = optionGroups.reduce((acc, group) => acc.concat(group.options), []);
  return (
    allOptions.find(
      ({rsin, domain}) => rsin === currentValue.rsin && domain === currentValue.domain
    ) ?? null
  );
};

const CatalogueSelect = ({loading, optionGroups}) => {
  const {
    values: {objectsApiGroup = null, catalogue = {}},
    getFieldHelpers,
  } = useFormikContext();

  const {setValue} = getFieldHelpers('catalogue');
  const value = extractValue(optionGroups, catalogue);
  return (
    <FormRow>
      <Field
        name="catalogue"
        label={
          <FormattedMessage
            description="Objects API registration options 'catalogue' label"
            defaultMessage="Catalogue"
          />
        }
        noManageChildProps
      >
        <ReactSelect
          name="catalogue"
          options={optionGroups}
          isLoading={loading}
          isDisabled={!objectsApiGroup}
          // override from the default because we're using an object as value
          value={value}
          onChange={selectedOption => {
            // set to undefined instead of null, this deletes the value from the formik
            // state
            setValue(selectedOption ?? undefined);
          }}
          getOptionValue={option => JSON.stringify(option)}
          isClearable
        />
      </Field>
    </FormRow>
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

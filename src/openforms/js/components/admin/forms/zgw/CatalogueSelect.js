import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

/**
 * @typedef {Object} Catalogue
 * @property {string} rsin - The RSIN identifier of the organisation owning the catalogue.
 * @property {string} label - A label to identify the catalogue in a dropdown.
 *
 * @typedef {Object} CatalogueGroup
 * @property {string} label
 * @property {Catalogue[]} options
 */

export const extractValue = (optionGroups, currentValue) => {
  const allOptions = optionGroups.reduce((acc, group) => acc.concat(group.options), []);
  return (
    allOptions.find(
      ({rsin, domain}) => rsin === currentValue.rsin && domain === currentValue.domain
    ) ?? null
  );
};

/**
 * Group options by organisation RSIN and sort them by label.
 * @param  {Catalogue[]} catalogues List of catalogues, typically retrieved from an API endpoint.
 * @return {CatalogueGroup[]} An array of catalogue groups. Each group contains the catalogues of each RSIN.
 */
export const groupAndSortOptions = catalogues => {
  const _optionsByRSIN = {};
  for (const catalogue of catalogues) {
    const {rsin} = catalogue;
    if (!_optionsByRSIN[rsin]) _optionsByRSIN[rsin] = [];
    _optionsByRSIN[rsin].push(catalogue);
  }

  const groups = Object.entries(_optionsByRSIN)
    .map(([rsin, options]) => ({
      label: rsin,
      options: options.sort((a, b) => a.label.localeCompare(b.label)),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return groups;
};

const CatalogueSelect = ({label, isDisabled = false, loading, optionGroups}) => {
  const {
    values: {catalogue = {}},
    getFieldHelpers,
  } = useFormikContext();

  const {setValue} = getFieldHelpers('catalogue');
  const value = extractValue(optionGroups, catalogue);
  return (
    <FormRow>
      <Field name="catalogue" label={label} noManageChildProps>
        <ReactSelect
          name="catalogue"
          options={optionGroups}
          isLoading={loading}
          isDisabled={isDisabled}
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

export const CatalogueSelectOptions = PropTypes.arrayOf(
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
);

CatalogueSelect.propTypes = {
  label: PropTypes.node.isRequired,
  isDisabled: PropTypes.bool,
  loading: PropTypes.bool.isRequired,
  optionGroups: CatalogueSelectOptions,
};

export default CatalogueSelect;

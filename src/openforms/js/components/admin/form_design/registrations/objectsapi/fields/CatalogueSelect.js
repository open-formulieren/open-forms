import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

const ENDPOINT = '/api/v2/registration/plugins/objects-api/catalogues';

const getCatalogues = async apiGroupID => {
  const response = await get(ENDPOINT, {objects_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available object type versions failed');
  }
  const catalogues = response.data;

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

const CatalogueSelect = () => {
  const {
    values: {objectsApiGroup = null, catalogue = {}},
    getFieldHelpers,
  } = useFormikContext();

  const {setValue} = getFieldHelpers('catalogue');

  const {
    loading,
    value: optionGroups = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    return await getCatalogues(objectsApiGroup);
  }, [objectsApiGroup]);
  if (error) throw error;

  const allOptions = optionGroups.reduce((acc, group) => acc.concat(group.options), []);
  const value =
    allOptions.find(({rsin, domain}) => rsin === catalogue.rsin && domain === catalogue.domain) ??
    null;
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

export default CatalogueSelect;

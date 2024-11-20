import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

const PRODUCTS_ENDPOINT = '/api/v2/registration/plugins/zgw-api/products';

const getAvailableProducts = async (apiGroupID, catalogueUrl, caseTypeIdentification) => {
  const response = await get(PRODUCTS_ENDPOINT, {
    zgw_api_group: apiGroupID,
    catalogue_url: catalogueUrl,
    case_type_identification: caseTypeIdentification,
  });
  if (!response.ok) {
    throw new Error('Loading available case type products failed');
  }
  return response.data.map(({url, description}) => ({
    value: url,
    label: description || url,
  }));
};

const ProductSelect = ({catalogueUrl = ''}) => {
  const {
    values: {zgwApiGroup = null, caseTypeIdentification = ''},
  } = useFormikContext();

  const {
    loading,
    value: options = [],
    error,
  } = useAsync(async () => {
    if (!zgwApiGroup || !catalogueUrl || !caseTypeIdentification) return [];
    return await getAvailableProducts(zgwApiGroup, catalogueUrl, caseTypeIdentification);
  }, [zgwApiGroup, catalogueUrl, caseTypeIdentification]);
  if (error) throw error;

  return (
    <FormRow>
      <Field
        name="productUrl"
        required={false}
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'product' label"
            defaultMessage="Product"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'product' helpText"
            defaultMessage="This product will be set on the created case."
          />
        }
        noManageChildProps
      >
        <ReactSelect
          name="productUrl"
          options={options}
          isLoading={loading}
          isDisabled={!caseTypeIdentification}
          required={false}
          isClearable
        />
      </Field>
    </FormRow>
  );
};

ProductSelect.propTypes = {
  catalogueUrl: PropTypes.string,
};

export default ProductSelect;

import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Loader from 'components/admin/Loader';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

import {PRODUCTS_ENDPOINT} from './constants';

const ProductFields = ({selectedProduct = null, onChange}) => {
  const {loading, value: products} = useAsync(async () => {
    try {
      const response = await get(PRODUCTS_ENDPOINT);
      if (!response.ok) {
        throw new Error('Error loading products');
      }
      return response.data;
    } catch (e) {
      console.error(e);
    }
  });

  if (loading) {
    return <Loader />;
  }

  const productChoices = products.map(product => [product.url, product.name]);
  return (
    <Fieldset
      title={<FormattedMessage description="Product fieldset title" defaultMessage="Product" />}
    >
      <FormRow>
        <Field
          name="form.product"
          label={<FormattedMessage description="Form product label" defaultMessage="Product" />}
        >
          <Select
            choices={productChoices}
            value={selectedProduct || ''}
            onChange={event => {
              const value = event.target.value || null; // cast empty strint to null
              onChange({target: {name: event.target.name, value}});
            }}
            allowBlank
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

ProductFields.propTypes = {
  selectedProduct: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

export default ProductFields;

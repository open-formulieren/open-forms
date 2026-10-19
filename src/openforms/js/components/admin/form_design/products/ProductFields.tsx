import React from 'react';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Loader from 'components/admin/Loader';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

import {FieldChangeEvent, Product} from '@/components/types';

import {PRODUCTS_ENDPOINT} from '../constants';

interface SelectedProduct {
  url: string;
  producttype: string | null;
}

export interface ProductFieldProps {
  selectedProduct?: SelectedProduct;
  onChange: (event: FieldChangeEvent) => void;
}

const ProductFields: React.FC<ProductFieldProps> = ({selectedProduct, onChange}) => {
  const {loading, value: products = []} = useAsync(async (): Promise<Product[]> => {
    try {
      const response = await get(PRODUCTS_ENDPOINT);
      if (!response.ok) {
        throw new Error('Error loading products');
      }
      return response.data;
    } catch (e) {
      throw new Error('Error loading products');
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
            value={selectedProduct?.url || ''}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              const value = event.target.value || null; // use empty string or null
              const product = !!value && products.find(({url}) => url === value);
              const selectedValue = product
                ? {url: product.url, producttype: product.producttype}
                : value;
              onChange({target: {name: event.target.name, value: selectedValue ?? ''}});
            }}
            allowBlank
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

export default ProductFields;

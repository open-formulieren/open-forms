import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import {get} from '../../../utils/fetch';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from '../forms/Select';
import Loader from '../Loader';

import {PRODUCTS_ENDPOINT} from './constants';

const ProductFields = ({ selectedProduct=null, onChange }) => {
    const {loading, value: products} = useAsync(
        async () => {
            try {
                const response = await get(PRODUCTS_ENDPOINT);
                if (!response.ok) {
                    throw new Error('Error loading products');
                }
                return response.data;
            } catch (e) {
                console.error(e);
            }
        }
    );

    if (loading) {
        return (<Loader />);
    }

    const productChoices = products.map(product => [product.url, product.name]);
    return (
        <Fieldset extraClassName="admin-fieldset">
            <FormRow>
                <Field
                    name="form.product"
                    label={<FormattedMessage description="Form product label" defaultMessage="Product" />}
                >
                    <Select
                        choices={productChoices}
                        value={selectedProduct || ''}
                        onChange={ (event) => {
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

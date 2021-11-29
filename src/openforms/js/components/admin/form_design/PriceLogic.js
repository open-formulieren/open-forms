import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, FormattedMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../utils/i18n';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from '../forms/Select';


export const EMPTY_PRICE_RULE = {
    uuid: '',
    form: '',
    jsonLogicTrigger: {},
    price: '',
};


const PRICING_MODES = [
    [
        'static',
        defineMessage({
            description: 'static pricing mode label',
            defaultMessage: 'Use linked product price',
        })
    ],
    [
        'dynamic',
        defineMessage({
            description: 'dynamic pricing mode label',
            defaultMessage: 'Use logic rules to determine the price',
        })
    ],
];


const PricingMode = ({ hasDynamicPricing, onChange }) => {
    const intl = useIntl();
    return (
        <Select
            choices={getTranslatedChoices(intl, PRICING_MODES)}
            value={hasDynamicPricing ? 'dynamic' : 'static'}
            onChange={onChange}
        />
    );
};

PricingMode.propTypes = {
    hasDynamicPricing: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
};


export const PriceLogic = ({ rules=[], availableComponents={}, onChange, onDelete, onAdd }) => {
    const hasDynamicPricing = rules.length > 0;

    const onPricingModeChange = (event) => {
        const {value} = event.target;
        // toggle from static to dynamic -> ensure at least one rule exists
        if (value === 'dynamic' && !hasDynamicPricing) {
            onAdd();
        // toggle from dynamic to static -> delete all the rules
        } else if (value === 'static' && hasDynamicPricing) {
            rules.forEach((rule, index) => onDelete(index));
        }
    };

    return (
        <Fieldset
            extraClassName="admin-fieldset"
            title={<FormattedMessage description="Dynamic pricing fieldset title" defaultMessage="Pricing logic" />}
        >

            <FormRow>
                <Field
                    name="pricing.mode"
                    label={<FormattedMessage description="Pricing mode label" defaultMessage="Mode" />}
                >
                    <PricingMode hasDynamicPricing={hasDynamicPricing} onChange={onPricingModeChange} />
                </Field>
            </FormRow>

        </Fieldset>
    );
};

PriceLogic.propTypes = {
    rules: PropTypes.arrayOf(PropTypes.object),
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
};


export default PriceLogic;

import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, FormattedMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../utils/i18n';
import {ComponentsContext} from '../forms/Context';
import Field from '../forms/Field';
import {NumberInput} from '../forms/Inputs';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from '../forms/Select';
import DeleteIcon from '../DeleteIcon';
import Trigger from './logic/Trigger';


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

    // TODO: de-duplicate/validate duplicate rules (identical triggers?)

    const onPricingModeChange = (event) => {
        const {value} = event.target;
        // toggle from static to dynamic -> ensure at least one rule exists
        if (value === 'dynamic' && !hasDynamicPricing) {
            onAdd();
        // toggle from dynamic to static -> delete all the rules
        } else if (value === 'static' && hasDynamicPricing) {
            // XXX: iterate in reverse so we delete all rules by removing the last one
            // every time.
            // State updates in event handlers are batched by React, so removing index 0, 1,...
            // in success causes issues since the local `rules` does no langer match the
            // parent component state - draft.priceRules.length !== rules.length.
            // By reversing, we essentially pop the last element every time which
            // works around this.
            const maxIndex = rules.length - 1;
            for (let offset=0; offset < rules.length; offset++) {
                onDelete(maxIndex - offset);
            }
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

            <ComponentsContext.Provider value={availableComponents}>
                {
                    rules.map((rule, i) => (
                        <Rule
                            key={i}
                            {...rule}
                            onChange={onChange.bind(null, i)}
                            onDelete={onDelete.bind(null, i)}
                        />
                    ))
                }
                <div className="button-container button-container--padded">
                    <button type="button" className="button button--plain" onClick={onAdd}>
                        <span className="addlink">
                            <FormattedMessage description="Add price logic rule button" defaultMessage="Add rule" />
                        </span>
                    </button>
                </div>
            </ComponentsContext.Provider>

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



const Rule = ({jsonLogicTrigger, price='', onChange, onDelete}) => {
    const intl = useIntl();
    const deleteConfirmMessage = intl.formatMessage({
        description: 'Price rule deletion confirm message',
        defaultMessage: 'Are you sure you want to delete this rule?',
    });
    return (
        <div className="logic-rule logic-rule--flat">
            <div className="logic-rule__actions">
                <DeleteIcon onConfirm={onDelete} message={deleteConfirmMessage} />
            </div>

            <div className="logic-rule__rule">
                <Trigger name="jsonLogicTrigger" logic={jsonLogicTrigger} onChange={onChange}>
                    <FormattedMessage description="Price logic prefix" defaultMessage="Then the price is" />
                    &nbsp;&euro;&nbsp;
                    <NumberInput name="price" value={price} min="0.00" step="any" onChange={onChange} />
                </Trigger>
            </div>
        </div>
    );
};

Rule.propTypes = {
    jsonLogicTrigger: PropTypes.object,
    price: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};

export default PriceLogic;

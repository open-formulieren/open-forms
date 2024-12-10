import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, defineMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {getTranslatedChoices} from 'utils/i18n';

const PRICING_MODES = [
  [
    'static',
    defineMessage({
      description: 'static pricing mode label',
      defaultMessage: 'Use linked product price',
    }),
  ],
  [
    'variable',
    defineMessage({
      description: 'variable pricing mode label',
      defaultMessage: 'Use a variable for the price',
    }),
  ],
];

const PricingMode = ({mode = 'static', onChange}) => {
  const intl = useIntl();
  return (
    <Select choices={getTranslatedChoices(intl, PRICING_MODES)} value={mode} onChange={onChange} />
  );
};

PricingMode.propTypes = {
  mode: PropTypes.oneOf(PRICING_MODES.map(item => item[0])),
  onChange: PropTypes.func.isRequired,
};

export const PriceLogic = ({variableKey, onFieldChange}) => {
  const initialPricingMode = variableKey !== '' ? 'variable' : 'static';
  const [pricingMode, setPricingMode] = useState(initialPricingMode);

  const onPricingModeChange = event => {
    const {value} = event.target;

    switch (value) {
      case 'variable': {
        break;
      }
      case 'static': {
        if (variableKey) {
          onFieldChange({target: {name: 'form.priceVariableKey', value: ''}});
        }
        break;
      }
    }

    setPricingMode(value);
  };

  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Dynamic pricing fieldset title"
          defaultMessage="Pricing logic"
        />
      }
    >
      <FormRow>
        <Field
          name="pricing.mode"
          label={<FormattedMessage description="Pricing mode label" defaultMessage="Mode" />}
        >
          <PricingMode mode={pricingMode} onChange={onPricingModeChange} />
        </Field>
      </FormRow>

      {pricingMode === 'variable' && (
        <FormRow>
          <Field
            name="form.priceVariableKey"
            label={
              <FormattedMessage description="Price variable label" defaultMessage="Variable" />
            }
          >
            <VariableSelection
              id="form_priceVariableKey"
              name="form.priceVariableKey"
              value={variableKey || ''}
              onChange={onFieldChange}
              filter={variable => {
                // See constant `DATATYPES_CHOICES` in
                // src/openforms/js/components/admin/form_design/variables/constants.js
                // XXX we *could* consider strings here but then they must be string
                // representations of numbers.
                return ['int', 'float'].includes(variable.dataType) || variable.key === variableKey;
              }}
            />
          </Field>
        </FormRow>
      )}
    </Fieldset>
  );
};

PriceLogic.propTypes = {
  variableKey: PropTypes.string.isRequired,
  onFieldChange: PropTypes.func.isRequired,
};

export default PriceLogic;

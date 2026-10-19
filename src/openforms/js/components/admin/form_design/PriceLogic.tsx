import React, {useState} from 'react';
import {FormattedMessage, MessageDescriptor, defineMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';
import VariableSelection from 'components/admin/forms/VariableSelection';

import {FieldChangeEvent, FormVariable} from '@/components/types';
import {getTranslatedChoices} from '@/utils/i18n';

import {WarningIcon} from '../icons';

const PRICING_MODES = {
  static: 'static',
  variable: 'variable',
} as const;

type PricingMode = (typeof PRICING_MODES)[keyof typeof PRICING_MODES];

const PRICING_MODE_TRANSLATIONS: [PricingMode, MessageDescriptor][] = [
  [
    PRICING_MODES.static,
    defineMessage({
      description: 'static pricing mode label',
      defaultMessage: 'Use linked product price',
    }),
  ],
  [
    PRICING_MODES.variable,
    defineMessage({
      description: 'variable pricing mode label',
      defaultMessage: 'Use a variable for the price',
    }),
  ],
];

interface PricingModeProps {
  id?: string;
  name?: string;
  mode: PricingMode;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  choices: Array<[PricingMode, MessageDescriptor]>;
  warning?: React.ReactNode;
}

const PricingMode: React.FC<PricingModeProps> = ({
  id,
  name,
  mode = PRICING_MODES.static,
  onChange,
  choices,
  warning,
}) => {
  const intl = useIntl();
  return (
    <>
      <Select
        id={id}
        name={name}
        choices={getTranslatedChoices(intl, choices)}
        value={mode}
        onChange={onChange}
      />
      {warning}
    </>
  );
};

interface PriceLogicProps {
  variableKey: string;
  onFieldChange: (event: FieldChangeEvent) => void;
  isOpenProduct: boolean;
}

export const PriceLogic: React.FC<PriceLogicProps> = ({
  variableKey,
  onFieldChange,
  isOpenProduct,
}) => {
  const initialPricingMode =
    variableKey !== '' && !isOpenProduct ? PRICING_MODES.variable : PRICING_MODES.static;
  const [pricingMode, setPricingMode] = useState(initialPricingMode);

  const onPricingModeChange = (event: FieldChangeEvent) => {
    const {value} = event.target;

    switch (value) {
      case PRICING_MODES.variable: {
        break;
      }
      case PRICING_MODES.static: {
        if (variableKey) {
          onFieldChange({target: {name: 'form.priceVariableKey', value: ''}});
        }
        break;
      }
    }

    setPricingMode(value as PricingMode);
  };

  const pricingModeChoices = PRICING_MODE_TRANSLATIONS.filter(([mode]) => {
    if (isOpenProduct && mode === PRICING_MODES.variable) {
      return false;
    }
    return true;
  });

  if (isOpenProduct && pricingMode != PRICING_MODES.static) {
    onPricingModeChange({target: {name: 'pricing.mode', value: PRICING_MODES.static}});
  }

  const intl = useIntl();
  const openProductWarningText = intl.formatMessage({
    description:
      'Warning message that informs the user can only select certain price logic modes when a Open Product product is selected.',
    defaultMessage:
      'Only "Use linked product price" mode is allowed when a Open Product product is selected.',
  });
  // Pass the WarningIcon component down to the PricingMode component so that the Field
  // component can pass the name and id attributes correctly to it's child element.
  const warning = isOpenProduct ? <WarningIcon text={openProductWarningText} /> : undefined;
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
          <PricingMode
            mode={pricingMode}
            onChange={onPricingModeChange}
            choices={pricingModeChoices}
            warning={warning}
          />
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
              filter={(variable: FormVariable) => {
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

export default PriceLogic;

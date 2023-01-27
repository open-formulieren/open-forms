import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, defineMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {NumberInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import {getTranslatedChoices} from 'utils/i18n';

// import UserDefinedVariables from 'components/admin/form_design/variables/UserDefinedVariables'
import DSLEditorNode from './logic/DSLEditorNode';
import Trigger from './logic/Trigger';
import {parseValidationErrors} from './utils';

export const EMPTY_PRICE_RULE = {
  uuid: '',
  _generatedId: '', // consumers should generate this, as it's used for the React key prop if no uuid exists
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
    }),
  ],
  [
    'dynamic',
    defineMessage({
      description: 'dynamic pricing mode label',
      defaultMessage: 'Use logic rules to determine the price',
    }),
  ],
  [
    'from_variable',
    defineMessage({
      description: 'variable pricing mode label',
      defaultMessage: 'Determine the price based on user-defined variable',
    }),
  ],
];

const PricingMode = ({pricingLogic, onChange}) => {
  const intl = useIntl();
  return (
    <Field name="form.pricingLogic">
      <Select
        choices={getTranslatedChoices(intl, PRICING_MODES)}
        value={pricingLogic}
        onChange={onChange}
      />
    </Field>
  );
};

const PricingVariable = ({formVariables, pricingVariable, onChange}) => {
  return (
    <Field
      name="form.pricingVariable"
      label={
        <FormattedMessage
          description="Pricing variable label"
          defaultMessage="Select pricing variable"
        />
      }
    >
      <Select
        // testing
        choices={[
          [formVariables[0].name, formVariables[0].name],
          [formVariables[1].name, formVariables[1].name],
        ]}
        value={pricingVariable}
        onChange={onChange}
      />
    </Field>
  );
};

PricingMode.propTypes = {
  onChange: PropTypes.func.isRequired,
};

export const PriceLogic = ({
  rules = [],
  formVariables,
  pricingLogic,
  pricingVariable,
  onChangePricingLogic,
  onChangePricingVariable,
  onChangePriceRule,
  onDelete,
  onAdd,
}) => {
  const hasDynamicPricing = rules.length > 0;

  const validationErrors = parseValidationErrors(useContext(ValidationErrorContext), 'priceRules');

  // TODO: de-duplicate/validate duplicate rules (identical triggers?)

  const onPricingModeChange = event => {
    onChangePricingLogic(event); // dispatch to onPricingLogicChange in form-creation.js
    const {value} = event.target;

    // toggle from static to dynamic -> ensure at least one rule exists
    if (value === 'dynamic' && !hasDynamicPricing) {
      onAdd();
      // toggle from dynamic to static -> delete all the rules
    } else if ((value === 'static' || value === 'from_variable') && hasDynamicPricing) {
      // XXX: iterate in reverse so we delete all rules by removing the last one
      // every time.
      // State updates in event handlers are batched by React, so removing index 0, 1,...
      // in success causes issues since the local `rules` does no langer match the
      // parent component state - draft.priceRules.length !== rules.length.
      // By reversing, we essentially pop the last element every time which
      // works around this.
      const maxIndex = rules.length - 1;
      for (let offset = 0; offset < rules.length; offset++) {
        onDelete(maxIndex - offset);
      }
    }

    pricingLogic = value;
  };

  return (
    <Fieldset
      extraClassName="admin-fieldset"
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
            pricingLogic={pricingLogic}
            hasDynamicPricing={hasDynamicPricing}
            onChange={onPricingModeChange}
          />
        </Field>
      </FormRow>
      {pricingLogic === 'from_variable' && (
        <PricingVariable
          formVariables={formVariables}
          pricingVariable={pricingVariable}
          onChange={onChangePricingVariable}
        />
      )}

      {rules.map((rule, index) => (
        <Rule
          key={rule.uuid || rule._generatedId}
          {...rule}
          onChange={onChangePriceRule.bind(null, index)}
          onDelete={onDelete.bind(null, index)}
          errors={validationErrors[index.toString()]}
        />
      ))}
      {hasDynamicPricing && (
        <ButtonContainer onClick={onAdd}>
          <FormattedMessage description="Add price logic rule button" defaultMessage="Add rule" />
        </ButtonContainer>
      )}
    </Fieldset>
  );
};

PriceLogic.propTypes = {
  rules: PropTypes.arrayOf(PropTypes.object),
  onChangePricingLogic: PropTypes.func.isRequired,
  onChangePricingVariable: PropTypes.func.isRequired,
  onChangePriceRule: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
};

const Rule = ({jsonLogicTrigger, price = '', onChange, onDelete, errors = {}}) => {
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
        <Trigger
          name="jsonLogicTrigger"
          logic={jsonLogicTrigger}
          onChange={onChange}
          error={errors.jsonLogicTrigger}
          withDSLPreview
        >
          <DSLEditorNode errors={errors.price}>
            <FormattedMessage description="Price logic prefix" defaultMessage="Then the price is" />
            &nbsp;&euro;&nbsp;
            <NumberInput name="price" value={price} min="0.00" step="any" onChange={onChange} />
          </DSLEditorNode>
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
  errors: PropTypes.object,
};

export default PriceLogic;

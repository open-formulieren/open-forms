import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, defineMessage, useIntl} from 'react-intl';
import {getTranslatedChoices} from 'utils/i18n';

import DeleteIcon from 'components/admin/DeleteIcon';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {NumberInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';

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
];

const PricingMode = ({hasDynamicPricing, onChange}) => {
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

export const PriceLogic = ({rules = [], onChange, onDelete, onAdd}) => {
  const hasDynamicPricing = rules.length > 0;

  const validationErrors = parseValidationErrors(useContext(ValidationErrorContext), 'priceRules');

  // TODO: de-duplicate/validate duplicate rules (identical triggers?)

  const onPricingModeChange = event => {
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
      for (let offset = 0; offset < rules.length; offset++) {
        onDelete(maxIndex - offset);
      }
    }
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
          <PricingMode hasDynamicPricing={hasDynamicPricing} onChange={onPricingModeChange} />
        </Field>
      </FormRow>

      {rules.map((rule, index) => (
        <Rule
          key={rule.uuid || rule._generatedId}
          {...rule}
          onChange={onChange.bind(null, index)}
          onDelete={onDelete.bind(null, index)}
          errors={validationErrors[index.toString()]}
        />
      ))}

      <ButtonContainer onClick={onAdd}>
        <FormattedMessage description="Add price logic rule button" defaultMessage="Add rule" />
      </ButtonContainer>
    </Fieldset>
  );
};

PriceLogic.propTypes = {
  rules: PropTypes.arrayOf(PropTypes.object),
  onChange: PropTypes.func.isRequired,
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

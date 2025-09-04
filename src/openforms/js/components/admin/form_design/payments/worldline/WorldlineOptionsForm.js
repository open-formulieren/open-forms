import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';
import {getChoicesFromSchema} from 'utils/json-schema';

import OptionsConfiguration from '../OptionsConfiguration';
import {Merchant} from './fields';

const WorldlineOptionsForm = ({schema, formData, onSubmit}) => {
  const validationErrors = useContext(ValidationErrorContext);

  const merchantChoices = getChoicesFromSchema(
    schema.properties.merchant.enum,
    schema.properties.merchant.enumNames
  ).map(([value, label]) => ({value, label}));

  const relevantErrors = filterErrors('form.paymentBackendOptions', validationErrors);

  return (
    <OptionsConfiguration
      numErrors={relevantErrors.length}
      modalTitle={
        <FormattedMessage
          description="Worldline options modal title"
          defaultMessage="Plugin configuration: Worldline"
        />
      }
      initialFormData={{
        merchant: null,
        ...formData,
      }}
      onSubmit={onSubmit}
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <Merchant options={merchantChoices} />
        </Fieldset>
      </ValidationErrorsProvider>
    </OptionsConfiguration>
  );
};

WorldlineOptionsForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.shape({
      merchant: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.string),
        enumNames: PropTypes.arrayOf(PropTypes.string),
      }),
    }),
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  formData: PropTypes.shape({
    merchant: PropTypes.string,
  }),
};

export default WorldlineOptionsForm;

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
import {ComTemplate, MerchantID, TitleTemplate} from './fields';

const OgoneLegacyOptionsForm = ({schema, formData, onSubmit}) => {
  const validationErrors = useContext(ValidationErrorContext);

  const merchantChoices = getChoicesFromSchema(
    schema.properties.merchantId.enum,
    schema.properties.merchantId.enumNames
  ).map(([value, label]) => ({value, label}));

  const relevantErrors = filterErrors('form.paymentBackendOptions', validationErrors);

  return (
    <OptionsConfiguration
      numErrors={relevantErrors.length}
      modalTitle={
        <FormattedMessage
          description="Ogone legacy options modal title"
          defaultMessage="Plugin configuration: Ogone legacy"
        />
      }
      initialFormData={{
        merchantId: null,
        ...formData,
      }}
      onSubmit={onSubmit}
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <MerchantID options={merchantChoices} />
          <TitleTemplate />
          <ComTemplate />
        </Fieldset>
      </ValidationErrorsProvider>
    </OptionsConfiguration>
  );
};

OgoneLegacyOptionsForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.shape({
      merchantId: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.number),
        enumNames: PropTypes.arrayOf(PropTypes.string),
      }),
    }),
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  formData: PropTypes.shape({
    merchantId: PropTypes.number,
  }),
};

export default OgoneLegacyOptionsForm;

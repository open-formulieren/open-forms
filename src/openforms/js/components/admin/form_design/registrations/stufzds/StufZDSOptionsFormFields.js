import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
} from 'components/admin/forms/ValidationErrors';

import CaseCode from './fields/CaseCode';
import CaseDescription from './fields/CaseDescription';
import CaseStatusCode from './fields/CaseStatusCode';
import CaseStatusDescription from './fields/CaseStatusDescription';
import DocumentConfidentialityLevel from './fields/DocumentConfidentialityLevel';
import DocumentDescription from './fields/DocumentDescription';
import PaymentStatusUpdateMapping from './fields/PaymentStatusUpdateMapping';
import {filterErrors, getChoicesFromSchema} from './utils';

const StufZDSOptionsFormFields = ({name, schema}) => {
  const validationErrors = useContext(ValidationErrorContext);

  const {zdsZaakdocVertrouwelijkheid} = schema.properties;
  const zdsZaakdocVertrouwelijkheidChoices = getChoicesFromSchema(
    zdsZaakdocVertrouwelijkheid.enum,
    zdsZaakdocVertrouwelijkheid.enumNames
  ).map(([value, label]) => ({value, label}));

  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Fieldset>
        <CaseCode />
        <CaseDescription />
        <CaseStatusCode />
        <CaseStatusDescription />
        <DocumentDescription />
        <DocumentConfidentialityLevel options={zdsZaakdocVertrouwelijkheidChoices} />
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="StUF-ZDS registration paymentStatusUpdateMapping label"
            defaultMessage="payment status update variable mapping"
          />
        }
        fieldNames={['paymentStatusUpdateMapping']}
      >
        <div className="description mb-2">
          <FormattedMessage
            description="StUF-ZDS registration paymentStatusUpdateMapping message"
            defaultMessage="This mapping is used to map the variable keys to keys used in the XML that is sent to StUF-ZDS. Those keys and the values belonging to them in the submission data are included in extraElementen."
          />
        </div>
        <PaymentStatusUpdateMapping />
      </Fieldset>
    </ValidationErrorsProvider>
  );
};

StufZDSOptionsFormFields.propTypes = {
  name: PropTypes.string.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};

export default StufZDSOptionsFormFields;

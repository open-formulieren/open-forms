import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';
import {getChoicesFromSchema} from 'utils/json-schema';

import CaseTypeCode from './fields/CaseTypeCode';
import CaseTypeDescription from './fields/CaseTypeDescription';
import DocumentConfidentialityLevel from './fields/DocumentConfidentialityLevel';
import DocumentTypeDescription from './fields/DocumentTypeDescription';
import StatusTypeCode from './fields/StatusTypeCode';
import StatusTypeDescription from './fields/StatusTypeDescription';
import VariablesMapping from './fields/VariablesMapping';

const StufZDSOptionsFormFields = ({name, schema}) => {
  const validationErrors = useContext(ValidationErrorContext);

  const {zdsZaakdocVertrouwelijkheid} = schema.properties;
  const zdsZaakdocVertrouwelijkheidChoices = getChoicesFromSchema(
    zdsZaakdocVertrouwelijkheid.enum,
    zdsZaakdocVertrouwelijkheid.enumNames
  ).map(([value, label]) => ({value, label}));

  const relevantErrors = filterErrors(name, validationErrors);
  const numVariablesMappingErrors = filterErrors(
    `${name}.variablesMapping`,
    validationErrors
  ).length;
  const numBaseErrors = relevantErrors.length - numVariablesMappingErrors;

  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Tabs>
        <TabList>
          <Tab hasErrors={numBaseErrors > 0}>
            <FormattedMessage
              description="StUF-ZDS registration backend options, 'base' tab label"
              defaultMessage="Base"
            />
          </Tab>
          <Tab hasErrors={numVariablesMappingErrors > 0}>
            <FormattedMessage
              description="StUF-ZDS registration backend options, 'extra elements' tab label"
              defaultMessage="Extra elements"
            />
          </Tab>
        </TabList>

        <TabPanel>
          <Fieldset>
            <CaseTypeCode />
            <CaseTypeDescription />
            <StatusTypeCode />
            <StatusTypeDescription />
            <DocumentTypeDescription />
            <DocumentConfidentialityLevel options={zdsZaakdocVertrouwelijkheidChoices} />
          </Fieldset>
        </TabPanel>

        <TabPanel>
          <Fieldset
            title={
              <FormattedMessage
                description="StUF-ZDS registration variablesMapping label"
                defaultMessage="Variables mapping"
              />
            }
            fieldNames={['variablesMapping']}
          >
            <div className="description">
              <FormattedMessage
                description="StUF-ZDS registration variablesMapping message"
                defaultMessage={`This mapping is used to map the variable keys to keys
                used in the XML that is sent to StUF-ZDS. Those keys and the values
                belonging to them in the submission data are included in <code>extraElementen</code>.
              `}
                values={{
                  code: chunks => <code>{chunks}</code>,
                }}
              />
            </div>
            <VariablesMapping />
          </Fieldset>
        </TabPanel>
      </Tabs>
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

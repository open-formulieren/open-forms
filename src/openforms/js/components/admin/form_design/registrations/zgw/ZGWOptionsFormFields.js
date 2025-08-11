import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

import BasicOptionsFieldset from './BasicOptionsFieldset';
import LegacyOptionsFieldset from './LegacyOptionsFieldset';
import ManageVariableToPropertyMappings from './ManageVariableToPropertyMappings';
import ObjectsAPIOptionsFieldset from './ObjectsAPIOptionsFieldset';
import OptionalOptionsFieldset from './OptionalOptionsFieldset';
import useCatalogueOptions from './useCatalogueOptions';

const ZGWFormFields = ({
  name,
  apiGroupChoices,
  objectsApiGroupChoices,
  confidentialityLevelChoices,
}) => {
  const {
    values: {propertyMappings = []},
  } = useFormikContext();
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  // load the available catalogues
  const {loadingCatalogues, catalogueOptionGroups, cataloguesError, catalogueUrl} =
    useCatalogueOptions();

  const numCasePropertyErrors = filterErrors(`${name}.propertyMappings`, validationErrors).length;
  const numBaseErrors = relevantErrors.length - numCasePropertyErrors;

  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Tabs>
        <TabList>
          <Tab hasErrors={numBaseErrors > 0}>
            <FormattedMessage
              description="ZGW APIs registration backend options, 'base' tab label"
              defaultMessage="Base"
            />
          </Tab>
          <Tab hasErrors={numCasePropertyErrors > 0}>
            <FormattedMessage
              description="ZGW APIs registration backend options, 'case properties' tab label"
              defaultMessage="Case properties ({count})"
              values={{
                count: propertyMappings.length,
              }}
            />
          </Tab>
        </TabList>

        {/* Base configuration */}
        <TabPanel>
          <BasicOptionsFieldset
            apiGroupChoices={apiGroupChoices}
            loadingCatalogues={loadingCatalogues}
            catalogueOptionGroups={catalogueOptionGroups}
            cataloguesError={cataloguesError}
            catalogueUrl={catalogueUrl}
          />
          <LegacyOptionsFieldset />
          <OptionalOptionsFieldset
            confidentialityLevelChoices={confidentialityLevelChoices}
            catalogueUrl={catalogueUrl}
          />
          <ObjectsAPIOptionsFieldset objectsApiGroupChoices={objectsApiGroupChoices} />
        </TabPanel>

        {/* zaakeigenschappen / case properties */}
        <TabPanel>
          <ManageVariableToPropertyMappings />
        </TabPanel>
      </Tabs>
    </ValidationErrorsProvider>
  );
};

ZGWFormFields.propTypes = {
  name: PropTypes.string,
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.number, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
  objectsApiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.string, // value
        PropTypes.string, // label
      ])
    )
  ),
  confidentialityLevelChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
};

export default ZGWFormFields;

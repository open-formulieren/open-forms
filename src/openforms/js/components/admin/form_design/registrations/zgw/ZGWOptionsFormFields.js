import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import {ContentJSON} from 'components/admin/form_design/registrations/objectsapi/LegacyConfigFields';
import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
} from 'components/admin/forms/ValidationErrors';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import ManageVariableToPropertyMappings from './ManageVariableToPropertyMappings';
import {
  CatalogueSelect,
  ConfidentialityLevel,
  DocumentType,
  LegacyCaseType,
  MedewerkerRoltype,
  ObjectType,
  ObjectTypeVersion,
  OrganisationRSIN,
  ZGWAPIGroup,
} from './fields';
import {filterErrors} from './utils';

const ZGWFormFields = ({name, apiGroupChoices, confidentialityLevelChoices}) => {
  const intl = useIntl();
  const {
    values: {
      zaaktype,
      informatieobjecttype,
      medewerkerRoltype,
      propertyMappings = [],
      objecttype,
      objecttypeVersion,
      contentJson,
    },
  } = useFormikContext();
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  const hasAnyFieldConfigured =
    [
      zaaktype,
      informatieobjecttype,
      medewerkerRoltype,
      objecttype,
      objecttypeVersion,
      contentJson,
    ].some(v => !!v) || propertyMappings.length > 0;

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
          <Fieldset>
            <ZGWAPIGroup
              apiGroupChoices={apiGroupChoices}
              onChangeCheck={() => {
                if (!hasAnyFieldConfigured) return true;
                const confirmSwitch = window.confirm(
                  intl.formatMessage({
                    description:
                      'ZGW APIs registration options: warning message when changing the api group',
                    defaultMessage: `Changing the api group will clear the existing configuration.
                    Are you sure you want to continue?`,
                  })
                );
                return confirmSwitch;
              }}
            />
            <ErrorBoundary
              errorMessage={
                <FormattedMessage
                  description="ZGW APIs registrations options: catalogue select error"
                  defaultMessage={`Something went wrong retrieving the available catalogues.
                    Please check that the services in the selected API group are configured correctly.`}
                />
              }
            >
              <CatalogueSelect />
            </ErrorBoundary>
          </Fieldset>

          <Fieldset
            title={
              <FormattedMessage
                description="ZGw APIs registration: legacy configuration options fieldset title"
                defaultMessage="Legacy configuration"
              />
            }
          >
            <div className="description">
              <FormattedMessage
                description="ZGW APIs legacy config options informative message"
                defaultMessage={`The configuration options here are legacy options. They
                will continue working, but you should upgrade to the new configuration
                options above. If a new configuration option is specified, the matching
                legacy option will be ignored.`}
              />
            </div>
            <LegacyCaseType />
            <DocumentType />
          </Fieldset>

          <Fieldset
            title={
              <FormattedMessage
                description="ZGW APIs registration: default overrides fieldset title"
                defaultMessage="Optional ZGW configuration"
              />
            }
            fieldNames={['organisatieRsin']}
          >
            <div className="description">
              <FormattedMessage
                description="ZGW APIs defaults override informative message"
                defaultMessage={`Any configuration option specified here overrides the
                matching option of the selected API group.`}
              />
            </div>
            <OrganisationRSIN />
            <ConfidentialityLevel options={confidentialityLevelChoices} />
            <MedewerkerRoltype />
          </Fieldset>

          <Fieldset
            title={
              <FormattedMessage
                description="ZGW APIs registration: Objects API fieldset title"
                defaultMessage="Objects API integration"
              />
            }
            collapsible
            fieldNames={['objecttype', 'objecttypeVersion', 'contentJson']}
          >
            <ObjectType />
            <ObjectTypeVersion />
            <ContentJSON />
          </Fieldset>
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
  confidentialityLevelChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
};

export default ZGWFormFields;

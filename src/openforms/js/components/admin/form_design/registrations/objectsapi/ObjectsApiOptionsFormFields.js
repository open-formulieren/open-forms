import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import {filterErrors} from 'components/admin/form_design/registrations/shared/utils';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
} from 'components/admin/forms/ValidationErrors';

import LegacyConfigFields from './LegacyConfigFields';
import V2ConfigFields from './V2ConfigFields';

const ObjectsApiOptionsFormFields = ({name, apiGroupChoices}) => {
  const intl = useIntl();
  const {values, setValues} = useFormikContext();
  const validationErrors = useContext(ValidationErrorContext);
  const {version = 1} = values;

  const v1SwitchMessage = intl.formatMessage({
    defaultMessage: `Switching to the legacy registration options will remove the existing variables mapping.
    Are you sure you want to continue?
    `,
    description: 'Objects API registration backend: v1 switch warning message',
  });

  const v2SwitchMessage = intl.formatMessage({
    defaultMessage: `Switching to the new registration options will remove the existing JSON templates.
    You will also not be able to save the form until the variables are correctly mapped.
    Are you sure you want to continue?
    `,
    description: 'Objects API registration backend: v2 switch warning message',
  });

  const changeVersion = tabIndex => {
    const newVersion = tabIndex + 1;

    // change form fields values depending on the newly selected version
    const newValues = {...values, version: newVersion};

    switch (newVersion) {
      case 1: {
        const confirmV1Switch = window.confirm(v1SwitchMessage);
        if (!confirmV1Switch) return;
        delete newValues.variablesMapping;
        delete newValues.geometryVariableKey;
        break;
      }
      case 2: {
        const confirmV2Switch = window.confirm(v2SwitchMessage);
        if (!confirmV2Switch) return;
        newValues.variablesMapping = [];
        newValues.geometryVariableKey = '';
        delete newValues.productaanvraagType;
        delete newValues.contentJson;
        delete newValues.paymentStatusUpdateJson;
        break;
      }
      default: {
        break;
      }
    }

    setValues(newValues);
  };

  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Tabs selectedIndex={version - 1} onSelect={changeVersion}>
        <TabList>
          <Tab>
            <FormattedMessage
              defaultMessage="Legacy"
              description="Objects API registration backend options 'Legacy' tab label"
            />
          </Tab>
          <Tab>
            <FormattedMessage
              defaultMessage="Variables Mapping"
              description="Objects API registration backend options 'Variables Mapping' tab label"
            />
          </Tab>
        </TabList>

        {/* Legacy format, template based */}
        <TabPanel>
          <LegacyConfigFields apiGroupChoices={apiGroupChoices} />
        </TabPanel>

        {/* Tight objecttypes integration */}
        <TabPanel>
          <V2ConfigFields apiGroupChoices={apiGroupChoices} />
        </TabPanel>
      </Tabs>
    </ValidationErrorsProvider>
  );
};

ObjectsApiOptionsFormFields.propTypes = {
  name: PropTypes.string,
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.number, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
};

export default ObjectsApiOptionsFormFields;

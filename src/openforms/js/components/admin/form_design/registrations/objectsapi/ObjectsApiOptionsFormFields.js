import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import useConfirm from 'components/admin/form_design/useConfirm';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

import LegacyConfigFields from './LegacyConfigFields';
import V2ConfigFields from './V2ConfigFields';

const VERSION_TO_INDEX_MAP = {
  2: 0, // first tab
  1: 1, // second tab
};

const INDEX_TO_VERSION_MAP = Object.fromEntries(
  Object.entries(VERSION_TO_INDEX_MAP).map(([version, index]) => [index, parseInt(version, 10)])
);

const ObjectsApiOptionsFormFields = ({name, apiGroupChoices}) => {
  const intl = useIntl();
  const {values, setValues} = useFormikContext();
  const validationErrors = useContext(ValidationErrorContext);
  const {version = 2} = values;

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

  const {
    ConfirmationModal: ConfirmationModalV1,
    confirmationModalProps: confirmationModalV1Props,
    openConfirmationModal: confirmUsingV1,
  } = useConfirm();
  const {
    ConfirmationModal: ConfirmationModalV2,
    confirmationModalProps: confirmationModalV2Props,
    openConfirmationModal: confirmUsingV2,
  } = useConfirm();

  const changeVersion = async tabIndex => {
    const newVersion = INDEX_TO_VERSION_MAP[tabIndex];

    // change form fields values depending on the newly selected version
    const newValues = {...values, version: newVersion};

    switch (newVersion) {
      case 1: {
        const confirmV1Switch = await confirmUsingV1();
        if (!confirmV1Switch) return;
        delete newValues.variablesMapping;
        delete newValues.geometryVariableKey;
        break;
      }
      case 2: {
        const confirmV2Switch = await confirmUsingV2();
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
      <Tabs selectedIndex={VERSION_TO_INDEX_MAP[version]} onSelect={changeVersion}>
        <TabList>
          <Tab>
            <FormattedMessage
              defaultMessage="Variables Mapping"
              description="Objects API registration backend options 'Variables Mapping' tab label"
            />
          </Tab>
          <Tab>
            <FormattedMessage
              defaultMessage="Legacy"
              description="Objects API registration backend options 'Legacy' tab label"
            />
          </Tab>
        </TabList>

        {/* Tight objecttypes integration */}
        <TabPanel>
          <V2ConfigFields apiGroupChoices={apiGroupChoices} />
        </TabPanel>

        {/* Legacy format, template based */}
        <TabPanel>
          <LegacyConfigFields apiGroupChoices={apiGroupChoices} />
        </TabPanel>
      </Tabs>
      <ConfirmationModalV1 {...confirmationModalV1Props} message={v1SwitchMessage} />
      <ConfirmationModalV2 {...confirmationModalV2Props} message={v2SwitchMessage} />
    </ValidationErrorsProvider>
  );
};

ObjectsApiOptionsFormFields.propTypes = {
  name: PropTypes.string,
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.string, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
};

export default ObjectsApiOptionsFormFields;

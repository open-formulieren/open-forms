import {useFormikContext} from 'formik';
import {useContext, useEffect} from 'react';

import {FormContext} from 'components/admin/form_design/Context';
import Fieldset from 'components/admin/forms/Fieldset';
import ValidationErrorsProvider, {
  ValidationErrorContext,
} from 'components/admin/forms/ValidationErrors';

import CustomerInteractionsAPIGroup from './CustomerInteractionsAPIGroup';
import ProfileFormVariable from './ProfileFormVariable';

const PLUGIN_ID = 'communication_preferences';

const defaults = {
  customerInteractionsApiGroup: null,
  profileFormVariable: '',
};

const CommunicationPreferencesFields = () => {
  const errors = Object.fromEntries(useContext(ValidationErrorContext));
  const optionsErrors = Object.entries(errors.options ?? {}).map(([key, errs]) => [
    `options.${key}`,
    errs,
  ]);

  const {values, setFieldValue} = useFormikContext();

  // Merge defaults into options if not already set
  useEffect(() => {
    const options = values.options ?? {};
    setFieldValue('options', {...defaults, ...options});
  }, []);

  const {
    plugins: {availablePrefillPlugins},
  } = useContext(FormContext);
  const communicationPreferencesPlugin = availablePrefillPlugins.find(
    elem => elem.id === PLUGIN_ID
  );
  const {apiGroups} = communicationPreferencesPlugin.configurationContext;

  return (
    <ValidationErrorsProvider errors={optionsErrors}>
      <Fieldset>
        <CustomerInteractionsAPIGroup
          name={'options.customerInteractionsApiGroup'}
          apiGroupChoices={apiGroups}
        />
        <ProfileFormVariable name={'options.profileFormVariable'} />
      </Fieldset>
    </ValidationErrorsProvider>
  );
};

export default CommunicationPreferencesFields;

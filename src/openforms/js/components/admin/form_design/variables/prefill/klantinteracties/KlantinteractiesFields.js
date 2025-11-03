import {useFormikContext} from 'formik';
import {useContext, useEffect} from 'react';

import Fieldset from 'components/admin/forms/Fieldset';
import ValidationErrorsProvider, {
  ValidationErrorContext,
} from 'components/admin/forms/ValidationErrors';
import ErrorMessage from 'components/errors/ErrorMessage';

import EmailField from './EmailField';
import PhoneNumberField from './PhoneNumberField';

const KlantinteractiesFields = () => {
  const {values, setFieldValue} = useFormikContext();
  const errors = Object.fromEntries(useContext(ValidationErrorContext));
  const optionsErrors = Object.entries(errors.options ?? {}).map(([key, errs]) => [
    `options.${key}`,
    errs,
  ]);
  const nonFieldErrors = optionsErrors.filter(([key]) => key === 'options.nonFieldErrors');

  const defaults = {
    email: false,
    phoneNumber: false,
  };

  // Merge defaults into options if not already set
  useEffect(() => {
    const options = values.options ?? {};
    setFieldValue('options', {...defaults, ...options});
  }, []);

  return (
    <ValidationErrorsProvider errors={optionsErrors}>
      {nonFieldErrors && (
        <>
          {nonFieldErrors.map(([field, message], index) => (
            <ErrorMessage key={`${field}-${index}`}>{message}</ErrorMessage>
          ))}
        </>
      )}
      <Fieldset>
        <EmailField />
        <PhoneNumberField />
      </Fieldset>
    </ValidationErrorsProvider>
  );
};

export default KlantinteractiesFields;

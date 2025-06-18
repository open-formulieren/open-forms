import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useEffect} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Radio, TextInput} from 'components/admin/forms/Inputs';
import RadioList from 'components/admin/forms/RadioList';

const StufZDSVariableConfigurationEditor = ({variable}) => {
  const intl = useIntl();
  const {values, getFieldProps, setFieldValue} = useFormikContext();
  const {variablesMapping = []} = values;

  let index = variablesMapping?.findIndex(
    mappedVariable => mappedVariable.variableKey === variable.key
  );

  if (index === -1) {
    // if not found, grab the next available index to add it as a new record/entry
    index = variablesMapping.length;
  }

  const namePrefix = `variablesMapping.${index}`;
  const mapped = values.variablesMapping?.[index] ?? {};
  const description = mapped?.description ?? '';

  const [field] = useField(`${namePrefix}.registerAs`);

  const registerAsOptions = [
    {
      id: 'zaakbetrokkene',
      label: intl.formatMessage({
        description: 'StUF-ZDS registration: register as zaakbetrokkene option',
        defaultMessage: 'Register as zaakbetrokkene',
      }),
    },
    {
      id: 'extraElementen',
      label: intl.formatMessage({
        description: 'StUF-ZDS registration: register as extraElementen option',
        defaultMessage: 'Register as extraElementen',
      }),
    },
  ];

  useEffect(() => {
    setFieldValue(`${namePrefix}.variableKey`, variable.key ?? '');

    if (!mapped.registerAs) {
      setFieldValue(`${namePrefix}.registerAs`, 'extraElementen');
    }
  }, [variable.key, mapped.registerAs, namePrefix, setFieldValue]);

  return (
    <Fieldset>
      <FormRow>
        <Field
          name={`${namePrefix}.variableKey`}
          label={
            <FormattedMessage description="'Variable key' label" defaultMessage="Variable key" />
          }
        >
          <TextInput
            {...getFieldProps(`${namePrefix}.variableKey`)}
            value={getFieldProps(`${namePrefix}.variableKey`).value ?? ''}
            readOnly
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.registerAs`}
          label={
            <FormattedMessage
              description="StUF-ZDS registration: registerAs label"
              defaultMessage="Register as"
            />
          }
          helpText={
            <FormattedMessage
              description="StUF-ZDS registration: select the type of registration."
              defaultMessage="Type of registration field help text"
            />
          }
        >
          <RadioList keyProp="registerAsType.id">
            {registerAsOptions.map((registerAsType, index) => (
              <Radio
                key={registerAsType.id}
                idFor={`id_${namePrefix}_${index}`}
                name={field.name}
                value={registerAsType.id}
                checked={field.value === registerAsType.id}
                onChange={field.onChange}
                label={registerAsType.label}
              />
            ))}
          </RadioList>
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`${namePrefix}.description`}
          label={
            <FormattedMessage
              description="StUF-ZDS registration: zaakbetrokkeneOmschrijving label"
              defaultMessage="Description"
            />
          }
          helpText={
            <FormattedMessage
              description="StUF-ZDS registration: zaakbetrokkeneOmschrijving help text."
              defaultMessage="The description for the object included in StUF-ZDS. 
              In case this is empty the value is taken from the variable's key by default."
            />
          }
        >
          <TextInput {...getFieldProps(`${namePrefix}.description`)} value={description} />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

StufZDSVariableConfigurationEditor.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
};

export {StufZDSVariableConfigurationEditor};

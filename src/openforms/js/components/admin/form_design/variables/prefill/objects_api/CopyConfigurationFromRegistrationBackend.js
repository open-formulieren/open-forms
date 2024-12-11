/**
 * Prefill configuration form specific to the Objects API prefill plugin.
 *
 * Most other plugins can be configured with the generic form in `./DefaultFields`.
 */
import {useField, useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import useConfirm from 'components/admin/form_design/useConfirm';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const CopyConfigurationFromRegistrationBackend = ({backends, onCopyDone}) => {
  const name = 'copyConfigurationFromBackend';
  const {setFieldValue, setValues} = useFormikContext();
  const options = backends.map(elem => ({value: elem.key, label: elem.name}));
  const [fieldProps] = useField(name);
  const {value} = fieldProps;
  const selectedBackend = backends.find(elem => elem.key === value);
  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();
  return (
    <FormRow>
      <Field
        name={name}
        label={
          <FormattedMessage
            description="Copy Objects API prefill configuration from registration backend label"
            defaultMessage="Copy configuration from registration backend"
          />
        }
        helpText={
          <FormattedMessage
            description="Copy Objects API prefill configuration from registration backend help text"
            defaultMessage="Select a registration backend and click the button to copy the configuration."
          />
        }
        noManageChildProps
      >
        <>
          <ReactSelect
            name={name}
            options={options}
            onChange={selectedOption => {
              setFieldValue(name, selectedOption.value);
            }}
            maxMenuHeight="16em"
          />

          <button
            type="button"
            className="button"
            onClick={async e => {
              e.preventDefault();
              const confirmSwitch = await openConfirmationModal();
              if (confirmSwitch) {
                setValues(prevValues => ({
                  ...prevValues,
                  // Trying to set multiple nested values doesn't work, since it sets them
                  // with dots in the key
                  options: {
                    ...prevValues.options,
                    objectsApiGroup: selectedBackend.options.objectsApiGroup,
                    objecttypeUuid: selectedBackend.options.objecttype,
                    objecttypeVersion: selectedBackend.options.objecttypeVersion,
                    authAttributePath: selectedBackend.options.authAttributePath,
                    variablesMapping: selectedBackend.options.variablesMapping,
                  },
                }));
                onCopyDone();
              }
            }}
            disabled={!selectedBackend}
            // admin style overrides...
            style={{
              marginLeft: '1em',
              paddingInline: '15px',
              paddingBlock: '7.5px',
              marginBlock: '0',
            }}
          >
            <FormattedMessage
              description="Copy Objects API prefill configuration from registration backend button"
              defaultMessage="Copy"
            />
          </button>
        </>
      </Field>

      <ConfirmationModal
        {...confirmationModalProps}
        message={
          <FormattedMessage
            description="Objects API prefill configuration: warning message when copying the config from registration backend"
            defaultMessage="Copying the configuration from the registration backend will clear the existing configuration. Are you sure you want to continue?"
          />
        }
      />
    </FormRow>
  );
};

export default CopyConfigurationFromRegistrationBackend;

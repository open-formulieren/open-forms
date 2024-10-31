import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const EmailHasAttachmentSelect = ({options}) => {
  const [{value}, , {setValue}] = useField('attachFilesToEmail');

  // React doesn't like null/undefined as it leads to uncontrolled component warnings,
  // so we translate null -> '' and vice versa in the change handler
  const normalizedValue = value === null ? '' : value;
  const normalizedOptions = options.map(option => ({
    ...option,
    value: option.value === null ? '' : option.value,
  }));

  return (
    <FormRow>
      <Field
        name="attachFilesToEmail"
        label={
          <FormattedMessage
            description="Email registration options 'attachFilesToEmail' label"
            defaultMessage="Attach files to email"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'attachFilesToEmail' helpText"
            defaultMessage="Enable to attach file uploads to the registration email. If set, this overrides the global default. Form designers should take special care to ensure that the total file upload sizes do not exceed the email size limit."
          />
        }
      >
        <ReactSelect
          name="attachFilesToEmail"
          options={normalizedOptions}
          value={normalizedOptions.find(option => option.value === normalizedValue)}
          required
          onChange={option => {
            // normalize empty string back to null
            const newValue = option.value === '' ? null : option.value;
            setValue(newValue);
          }}
        />
      </Field>
    </FormRow>
  );
};
EmailHasAttachmentSelect.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.bool,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export default EmailHasAttachmentSelect;

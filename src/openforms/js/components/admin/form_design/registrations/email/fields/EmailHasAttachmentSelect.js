import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const EmailHasAttachmentSelect = ({options}) => {
  const [fieldProps, , fieldHelpers] = useField('attachFilesToEmail');
  const {setValue} = fieldHelpers;

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
          options={options}
          value={options.find(option => option.value === fieldProps.value)}
          required
          onChange={newValue => {
            setValue(newValue.value);
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

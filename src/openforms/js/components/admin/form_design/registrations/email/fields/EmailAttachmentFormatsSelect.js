import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const EmailAttachmentFormatsSelect = ({options}) => {
  const [fieldProps, , fieldHelpers] = useField('attachmentFormats');
  const {setValue} = fieldHelpers;

  const values = [];
  if (fieldProps.value && fieldProps.value.length) {
    fieldProps.value.forEach(item => {
      const selectedOption = options.find(option => option.value === item);
      if (selectedOption) {
        values.push(selectedOption);
      }
    });
  }

  return (
    <FormRow>
      <Field
        name="attachmentFormats"
        label={
          <FormattedMessage
            description="Email registration options 'attachmentFormats' label"
            defaultMessage="The format(s) of the attachment(s) containing the submission details"
          />
        }
      >
        <ReactSelect
          name="attachmentFormats"
          options={options}
          isMulti
          required
          value={values}
          onChange={newValue => {
            setValue(newValue.map(item => item.value));
          }}
        />
      </Field>
    </FormRow>
  );
};

EmailAttachmentFormatsSelect.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export default EmailAttachmentFormatsSelect;

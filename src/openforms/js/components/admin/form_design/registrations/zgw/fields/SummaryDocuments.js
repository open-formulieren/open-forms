import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const SummaryDocuments = ({summaryDocumentChoices}) => {
  const [fieldProps] = useField('summaryDocuments');
  const {name: fieldName, value: initialValue, onChange} = fieldProps;

  return (
    <FormRow>
      <Field
        name="summaryDocuments"
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'summaryDocuments' label"
            defaultMessage="Summary documents"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'summaryDocuments' help text"
            defaultMessage="Which summary documents to include during registration."
          />
        }
      >
        <ul>
          {summaryDocumentChoices.map(([value, label], index) => (
            <li key={index}>
              <Checkbox
                key={index}
                label={label}
                value={value}
                name={fieldName}
                checked={initialValue ? initialValue.includes(value) : false}
                onChange={onChange}
              />
            </li>
          ))}
        </ul>
      </Field>
    </FormRow>
  );
};

SummaryDocuments.propTypes = {
  summaryDocumentChoices: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)).isRequired,
};

export default SummaryDocuments;

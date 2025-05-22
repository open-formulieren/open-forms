import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import VariableSelection from 'components/admin/forms/VariableSelection';

import {PERSON_TYPE_CHOICES} from './constants';

const PersonFields = ({type, mutableDataFormVariable}) => {
  const intl = useIntl();
  const {getFieldProps, setValues} = useFormikContext();

  const availableOptions = Object.entries(PERSON_TYPE_CHOICES).map(([value, msg]) => ({
    value,
    label: intl.formatMessage(msg),
  }));

  return (
    <Fieldset>
      <FormRow>
        <Field
          name="type"
          label={
            <FormattedMessage
              description="Family members options: 'Type' label"
              defaultMessage="Type"
            />
          }
          helpText={
            <FormattedMessage
              description="Family members options: 'Type' helpText"
              defaultMessage="The data will be retrieved for the selected type of person."
            />
          }
          required
        >
          <ReactSelect
            name="type"
            required
            options={availableOptions}
            value={availableOptions.find(opt => opt.value === type)}
            onChange={selectedOption => {
              const newValue = selectedOption ? selectedOption.value : null;
              // make sure the options have the right values when the type changes
              setValues(prevValues => ({
                ...prevValues,
                options: {
                  type: newValue,
                  mutableDataFormVariable: '',
                  minAge: null,
                  maxAge: null,
                  includeDeceased: true,
                },
              }));
            }}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="options.mutableDataFormVariable"
          label={
            <FormattedMessage
              description="Family members options: data destination form variable label"
              defaultMessage="Data destination form variable"
            />
          }
          required
        >
          <VariableSelection
            {...getFieldProps(mutableDataFormVariable)}
            value={mutableDataFormVariable}
            aria-label={
              <FormattedMessage
                description="Family members options: accessible label for (form) variable dropdown"
                defaultMessage="Data destination form variable"
              />
            }
            filter={variable => variable.dataType === 'array'}
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

PersonFields.propTypes = {
  type: PropTypes.string,
  mutableDataFormVariable: PropTypes.string,
};

export default PersonFields;

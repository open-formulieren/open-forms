import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import {useUpdateEffect} from 'react-use';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

const ObjectsAPIGroup = ({apiGroupChoices, onChangeCheck}) => {
  const [{onChange: onChangeFormik, ...fieldProps}, , {setValue}] = useField('objectsApiGroup');
  const {values, setValues} = useFormikContext();
  const {value} = fieldProps;

  // reset the objecttype specific-configuration whenever the API group changes
  useUpdateEffect(() => {
    const newValues = {
      ...values,
      objecttype: '',
      objecttypeVersion: undefined,
      variablesMapping: [],
    };
    setValues(newValues);
  }, [setValues, value]); // deliberately excluding values!

  const onChange = event => {
    const okToProceed = onChangeCheck === undefined || onChangeCheck();
    if (okToProceed) {
      // overridden to handle the proper data type, since very <option value>
      // turns into a string in HTML
      const newValue = event.currentTarget.value;
      const newId = newValue ? parseInt(newValue, 10) : null;
      setValue(newId);
    }
  };

  return (
    <FormRow>
      <Field
        name="objectsApiGroup"
        required
        label={
          <FormattedMessage
            description="Objects API group field label"
            defaultMessage="API group"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API group field help text"
            defaultMessage="The API group specifies which objects and objecttypes services to use."
          />
        }
        // errors={errors.objectsApiGroup}
      >
        <Select
          allowBlank
          choices={apiGroupChoices}
          id="id_objectsApiGroup"
          {...fieldProps}
          onChange={onChange}
        />
      </Field>
    </FormRow>
  );
};

ObjectsAPIGroup.propTypes = {
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.number, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
  onChangeCheck: PropTypes.func,
};

export default ObjectsAPIGroup;

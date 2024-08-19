import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import {useUpdateEffect} from 'react-use';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const ObjectsAPIGroup = ({apiGroupChoices, onChangeCheck}) => {
  const [{onChange: onChangeFormik, ...fieldProps}, , {setValue}] = useField('objectsApiGroup');
  const {setValues} = useFormikContext();
  const {value} = fieldProps;

  // reset the objecttype specific-configuration whenever the API group changes
  useUpdateEffect(() => {
    setValues(prevValues => ({
      ...prevValues,
      objecttype: '',
      objecttypeVersion: undefined,
      variablesMapping: [],
    }));
  }, [setValues, value]);

  const options = apiGroupChoices.map(([value, label]) => ({value, label}));
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
        noManageChildProps
      >
        <ReactSelect
          name="objectsApiGroup"
          options={options}
          required
          onChange={selectedOption => {
            const okToProceed = onChangeCheck === undefined || onChangeCheck();
            if (okToProceed) setValue(selectedOption.value);
          }}
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

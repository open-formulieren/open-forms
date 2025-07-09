import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import {useUpdateEffect} from 'react-use';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const ZGWAPIGroup = ({apiGroupChoices, onChangeCheck}) => {
  const [{onChange: onChangeFormik, ...fieldProps}, , {setValue}] = useField('zgwApiGroup');
  const {setValues} = useFormikContext();
  const {value} = fieldProps;

  // reset the zaaktype/objecttype specific-configuration whenever the API group changes
  useUpdateEffect(() => {
    setValues(prevValues => ({
      ...prevValues,
      caseTypeIdentification: '',
      documentTypeDescription: '',
      zaaktype: '',
      informatieobjecttype: '',
      medewerkerRoltype: '',
      partnersRoltype: '',
      partnersDescription: '',
      propertyMappings: [],
      // objects API integration
      objecttype: undefined,
      objecttypeVersion: undefined,
      contentJson: undefined,
    }));
  }, [setValues, value]);

  const options = apiGroupChoices.map(([value, label]) => ({value, label}));
  return (
    <FormRow>
      <Field
        name="zgwApiGroup"
        required
        label={
          <FormattedMessage description="ZGW APIs group field label" defaultMessage="API group" />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs group field help text"
            defaultMessage="The API group specifies which ZGW services to use."
          />
        }
        noManageChildProps
      >
        <ReactSelect
          name="zgwApiGroup"
          options={options}
          required
          onChange={async selectedOption => {
            const okToProceed = onChangeCheck === undefined || (await onChangeCheck());
            if (okToProceed) setValue(selectedOption?.value);
          }}
        />
      </Field>
    </FormRow>
  );
};

ZGWAPIGroup.propTypes = {
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

export default ZGWAPIGroup;

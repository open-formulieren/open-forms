import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {NumberInput} from 'components/admin/forms/Inputs';

/**
 * @todo - deprecate in favour of dropdown like in the objects API
 * @todo - make required if an object type is selected?
 */
const ObjectTypeVersion = () => {
  const [fieldProps] = useField('objecttypeVersion');
  return (
    <FormRow>
      <Field
        name="objecttypeVersion"
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'objecttypeVersion' label"
            defaultMessage="Version"
          />
        }
      >
        <NumberInput id="id_objecttype" min="1" step="1" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

ObjectTypeVersion.propTypes = {};

export default ObjectTypeVersion;

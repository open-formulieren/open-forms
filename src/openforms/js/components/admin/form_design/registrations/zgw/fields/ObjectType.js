import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

/**
 * @todo - deprecate in favour of dropdown like in the objects API
 */
const ObjectType = () => {
  const [fieldProps] = useField('objecttype');
  return (
    <FormRow>
      <Field
        name="objecttype"
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'objecttype' label"
            defaultMessage="Objecttype"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'objecttype' help text"
            defaultMessage={`URL to the object type in the objecttypes API.
            If provided, an object will be created and a case object relation will be
            added to the case.`}
          />
        }
      >
        <TextInput id="id_objecttype" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

ObjectType.propTypes = {};

export default ObjectType;

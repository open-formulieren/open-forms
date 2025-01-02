import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import {AuthAttributePath as SharedAuthAttributePath} from 'components/admin/forms/objects_api';

const AuthAttributePath = () => {
  const {
    values: {
      objectsApiGroup = null,
      objecttype = '',
      objecttypeVersion = null,
      updateExistingObject = false,
    },
  } = useFormikContext();
  return (
    <SharedAuthAttributePath
      name={'authAttributePath'}
      objectsApiGroup={objectsApiGroup}
      objecttypeUuid={objecttype}
      objecttypeVersion={objecttypeVersion}
      disabled={!updateExistingObject}
      required={updateExistingObject}
      helpText={
        <FormattedMessage
          description="Objects API registration: authAttributePath helpText"
          defaultMessage={`The property that gets compared with the identifier (e.g.
        BSN/KVK) of the authenticated user to verify ownership of the object being
        updated. This is important to prevent malicious users modifying information
        of other people than themselves.`}
        />
      }
    />
  );
};

export default AuthAttributePath;

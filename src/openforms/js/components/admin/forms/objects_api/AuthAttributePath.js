import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {useAsync} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TargetPathSelect} from 'components/admin/forms/objects_api';
import {post} from 'utils/fetch';

const AuthAttributePath = ({
  name,
  errors,
  objectsApiGroup,
  objecttypeUuid,
  objecttypeVersion,
  disabled = false,
  required = false,
  helpText = undefined,
}) => {
  const intl = useIntl();
  const {csrftoken} = useContext(APIContext);
  const {
    loading,
    value: targetPaths = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup || !objecttypeUuid || !objecttypeVersion) return [];
    const response = await post(REGISTRATION_OBJECTS_TARGET_PATHS, csrftoken, {
      objectsApiGroup,
      objecttype: objecttypeUuid,
      objecttypeVersion,
      variableJsonSchema: {type: 'string'},
    });
    if (!response.ok) {
      throw new Error('Error when loading target paths');
    }
    return response.data;
  }, [objectsApiGroup, objecttypeUuid, objecttypeVersion]);
  if (error) throw error; // bubble up to nearest error boundary

  // An object type (and particular version) must be selected before you can select
  // a targetpath, since it grabs the available properties from the objecttype json
  // schema definition.
  const noObjectTypeSelectedMessage = intl.formatMessage({
    description:
      'Object type target path selection for auth attribute message for missing options because no object type has been selected.',
    defaultMessage: 'Select an object type and version before you can pick a source path.',
  });

  return (
    <FormRow>
      <Field
        name={name}
        errors={errors}
        label={
          <FormattedMessage
            description="Objects API registration: authAttributePath label"
            defaultMessage="Owner identifier"
          />
        }
        helpText={helpText}
        disabled={disabled}
        required={required}
      >
        <TargetPathSelect
          name={name}
          isLoading={loading}
          targetPaths={targetPaths}
          isDisabled={disabled}
          noOptionsMessage={!objecttypeVersion ? () => noObjectTypeSelectedMessage : undefined}
        />
      </Field>
    </FormRow>
  );
};

AuthAttributePath.propTypes = {
  name: PropTypes.string.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  objectsApiGroup: PropTypes.string,
  objecttypeUuid: PropTypes.string,
  objecttypeVersion: PropTypes.number,
  disabled: PropTypes.bool,
  required: PropTypes.bool,
  helpText: PropTypes.node,
};

export default AuthAttributePath;

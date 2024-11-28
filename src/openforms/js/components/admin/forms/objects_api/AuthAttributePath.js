import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {LOADING_OPTION} from 'components/admin/forms/Select';
import {TargetPathDisplay, TargetPathSelect} from 'components/admin/forms/objects_api';
import {post} from 'utils/fetch';

const AuthAttributePath = ({
  name,
  errors,
  objectsApiGroup,
  objecttypeUuid,
  objecttypeVersion,
  disabled = false,
}) => {
  const [fieldProps] = useField({name: name, type: 'array'});
  const {csrftoken} = useContext(APIContext);
  const {
    loading,
    value: targetPaths,
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

  const choices =
    loading || error
      ? LOADING_OPTION
      : targetPaths.map(t => [JSON.stringify(t.targetPath), <TargetPathDisplay target={t} />]);

  return (
    <FormRow>
      <Field
        name={name}
        errors={errors}
        label={
          <FormattedMessage
            description="Objects API registration: authAttributePath label"
            defaultMessage="Path to auth attribute (e.g. BSN/KVK) in objects"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration: authAttributePath helpText"
            defaultMessage="This is used to perform validation to verify that the authenticated user is the owner of the object."
          />
        }
        disabled={disabled}
      >
        <TargetPathSelect name={name} index={1} choices={choices} value={fieldProps.value} />
      </Field>
    </FormRow>
  );
};

AuthAttributePath.propTypes = {
  name: PropTypes.string.isRequired,
  errors: PropTypes.arrayOf(PropTypes.string),
  objectsApiGroup: PropTypes.number,
  objecttypeUuid: PropTypes.string,
  objecttypeVersion: PropTypes.number,
  disabled: PropTypes.bool,
};

export default AuthAttributePath;

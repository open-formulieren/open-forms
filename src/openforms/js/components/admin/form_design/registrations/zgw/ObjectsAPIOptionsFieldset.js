import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import {ContentJSON} from 'components/admin/form_design/registrations/objectsapi/LegacyConfigFields';
import Fieldset from 'components/admin/forms/Fieldset';
import {ObjectsAPIGroup} from 'components/admin/forms/objects_api';

import {ObjectType, ObjectTypeVersion} from './fields';

/**
 * Callback to invoke when the API group changes - used to reset the dependent fields.
 */
const onApiGroupChange = prevValues => ({
  ...prevValues,
  objecttype: '',
  objecttypeVersion: undefined,
});

/**
 * Configuration fields related to the Objects API (template based) integration.
 */
const ObjectsAPIOptionsFieldset = ({objectsApiGroupChoices}) => {
  const {
    values: {objecttype = ''},
  } = useFormikContext();
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="ZGW APIs registration: Objects API fieldset title"
          defaultMessage="Objects API integration"
        />
      }
      collapsible
      fieldNames={['objecttype', 'objecttypeVersion', 'contentJson']}
    >
      <ObjectsAPIGroup
        apiGroupChoices={objectsApiGroupChoices}
        onApiGroupChange={onApiGroupChange}
        required={!!objecttype}
        isClearable
      />
      <ObjectType />
      <ObjectTypeVersion />
      <ContentJSON />
    </Fieldset>
  );
};

ObjectsAPIOptionsFieldset.propTypes = {
  objectsApiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.string, // value
        PropTypes.string, // label
      ])
    )
  ),
};

export default ObjectsAPIOptionsFieldset;

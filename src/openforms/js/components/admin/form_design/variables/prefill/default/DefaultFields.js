import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {LOADING_OPTION} from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

import AttributeField from './AttributeField';
import IdentifierRoleField from './IdentifierRoleField';

// Load the possible prefill attributes
// XXX: this would benefit from client-side caching
const getAttributes = async plugin => {
  if (!plugin) return [];

  const endpoint = `/api/v2/prefill/plugins/${plugin}/attributes`;
  // XXX: clean up error handling here at some point...
  const response = await get(endpoint);
  if (!response.ok) throw response.data;
  return response.data.map(attribute => [attribute.id, attribute.label]);
};

/**
 * Default (legacy) prefill configuration - after selecting the plugin, the user
 * selects which attribute to use to grab the prefill value from.
 */
const DefaultFields = () => {
  const {
    values: {plugin = ''},
  } = useFormikContext();
  const {
    loading,
    value = [],
    error,
  } = useAsync(async () => {
    try {
      return await getAttributes(plugin);
    } catch (e) {
      throw e;
    }
  }, [plugin]);

  // throw errors to the nearest error boundary
  if (error) throw error;
  const prefillAttributes = loading ? LOADING_OPTION : value;

  return (
    <Fieldset>
      <FormRow>
        <Field
          name="attribute"
          label={
            <FormattedMessage
              description="Variable prefill attribute label"
              defaultMessage="Attribute"
            />
          }
        >
          <AttributeField prefillAttributes={prefillAttributes} />
        </Field>
      </FormRow>

      <FormRow>
        <Field
          name="identifierRole"
          label={
            <FormattedMessage
              description="Variable prefill identifier role label"
              defaultMessage="Identifier role"
            />
          }
        >
          <IdentifierRoleField />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

DefaultFields.propTypes = {};

export default DefaultFields;

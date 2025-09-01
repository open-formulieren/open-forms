import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Alert from 'components/admin/Alert';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {LOADING_OPTION} from 'components/admin/forms/Select';
import {WarningIcon} from 'components/admin/icons';
import {get} from 'utils/fetch';

import AttributeField from '../default/AttributeField';
import IdentifierRoleField from '../default/IdentifierRoleField';

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
 * Copy of the Default prefill plugin fields, with an added Alert message to clarify its
 * usage.
 */
const EidasFields = () => {
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
      <Alert type="warning">
        <WarningIcon asLead />
        <FormattedMessage
          description="eIDAS prefill plugin warning message"
          defaultMessage="The eIDAS prefill plugin only works in conjunction with the eIDAS authentication plugin. Make sure to also configure the eIDAS authentication plugin!"
        />
      </Alert>
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

EidasFields.propTypes = {};

export default EidasFields;

import {useContext, useMemo} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';

import AttributeField from '../default/AttributeField';

const PLUGIN_ID = 'yivi';

const getPrefillAttributes = (prefillPlugins, authBackends) => {
  const prefillAttributes = [];
  const yiviPlugin = prefillPlugins.find(elem => elem.id === PLUGIN_ID);
  // shouldn't happen, but just in case... don't crash the entire component
  if (!yiviPlugin) return prefillAttributes;

  const {
    configurationContext: {fixedAttributes},
    requiresAuthPlugin,
  } = yiviPlugin;

  // figure out which authentication options are requested in the Yivi authentication
  // plugin configuration and which attribute groups may be filled
  const relevantAuthBackends = authBackends.filter(authBackend =>
    requiresAuthPlugin.includes(authBackend.backend)
  );
  const availableAuthOptions = [];
  const attributeGroupIds = [];
  relevantAuthBackends.forEach(({options: {authenticationOptions, additionalAttributesGroups}}) => {
    availableAuthOptions.push(...authenticationOptions);
    attributeGroupIds.push(...additionalAttributesGroups);
  });

  fixedAttributes.forEach(({attribute, label, authAttribute}) => {
    if (authAttribute && !availableAuthOptions.includes(authAttribute)) {
      return;
    }
    prefillAttributes.push([attribute, label]);
  });

  return prefillAttributes;
};

const YiviFields = () => {
  const {
    form: {authBackends = []},
    plugins: {availablePrefillPlugins},
  } = useContext(FormContext);
  const prefillAttributes = useMemo(
    () => getPrefillAttributes(availablePrefillPlugins, authBackends),
    [availablePrefillPlugins, authBackends]
  );
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
      {/* identifier role is deliberately omitted */}
    </Fieldset>
  );
};

export default YiviFields;

import {useContext, useMemo} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {useGetYiviAttributeGroups} from 'components/admin/forms/yivi/AttributeGroups';

import AttributeField from '../default/AttributeField';

const PLUGIN_ID = 'yivi';

export const getPrefillAttributes = (prefillPlugins, authBackends, attributeGroups) => {
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

  // add the attributes from the attribute groups, taking care to de-duplicate and sort
  // them. we only consider attribute groups that are included in the auth plugin options
  const uniqueAttributes = Array.from(
    new Set(
      attributeGroups
        .filter(attrGroup => attributeGroupIds.includes(attrGroup.uuid))
        .reduce((acc, attrGroup) => [...acc, ...attrGroup.attributes], [])
    )
  ).sort((a, b) => a.localeCompare(b));
  prefillAttributes.push(...uniqueAttributes.map(attr => [attr, attr]));

  return prefillAttributes;
};

const YiviFields = () => {
  const {
    form: {authBackends = []},
    plugins: {availablePrefillPlugins},
  } = useContext(FormContext);
  const {availableYiviAttributeGroups, error} = useGetYiviAttributeGroups();
  const prefillAttributes = useMemo(
    () => getPrefillAttributes(availablePrefillPlugins, authBackends, availableYiviAttributeGroups),
    [availablePrefillPlugins, authBackends, availableYiviAttributeGroups]
  );
  if (error) throw error;

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
          helpText={
            <FormattedMessage
              description="Yivi prefill attribute help text"
              defaultMessage={`Available attributes based on the configured Yivi
              authentication plugin options. The identifier attributes are fixed,
              while the remaining attributes are taken from the configured
              attribute groups.`}
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

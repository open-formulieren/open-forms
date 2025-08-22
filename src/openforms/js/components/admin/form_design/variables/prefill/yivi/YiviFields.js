import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import Alert from 'components/admin/Alert';
import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {WarningIcon} from 'components/admin/icons';

import AttributeField from '../default/AttributeField';
import IdentifierRoleField from '../default/IdentifierRoleField';

const YiviFields = () => {
  const {authBackends, yiviPrefillAttributes} = useContext(FormContext);
  const yiviAuthBackend = authBackends.find(authBackend => authBackend.backend === 'yivi_oidc');
  const {
    options: {additionalAttributesGroups},
  } = yiviAuthBackend;

  const getPrefillAttributes = expression => {
    const attributeGroup = yiviPrefillAttributes.find(expression);
    if (!attributeGroup || !Array.isArray(attributeGroup.attributes)) {
      return [];
    }

    return attributeGroup.attributes.map(attribute => [attribute.value, attribute.label]);
  };

  // The virtual attributes aren't dependent on the Yivi auth backend options, so they be
  // always added.
  const prefillAttributes = [...getPrefillAttributes(attributeGroup => attributeGroup.isStatic)];
  additionalAttributesGroups.forEach(groupUuid => {
    prefillAttributes.push(
      ...getPrefillAttributes(attributeGroup => attributeGroup.attributeGroupUuid === groupUuid)
    );
  });

  return (
    <Fieldset>
      <Alert type="warning">
        <WarningIcon asLead />
        <FormattedMessage
          description="Yivi prefill plugin warning message"
          defaultMessage="The Yivi prefill plugin only works in conjunction with the Yivi authentication plugin. Make sure to also configure the Yivi authentication plugin!"
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

export default YiviFields;

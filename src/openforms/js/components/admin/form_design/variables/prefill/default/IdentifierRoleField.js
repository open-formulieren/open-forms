import {useField} from 'formik';

import Select from 'components/admin/forms/Select';

import {IDENTIFIER_ROLE_CHOICES} from '../../constants';

const IdentifierRoleField = () => {
  const [fieldProps] = useField('identifierRole');
  const choices = Object.entries(IDENTIFIER_ROLE_CHOICES);
  return (
    <Select
      choices={choices}
      id="id_identifierRole"
      translateChoices
      capfirstChoices
      {...fieldProps}
    />
  );
};

export default IdentifierRoleField;

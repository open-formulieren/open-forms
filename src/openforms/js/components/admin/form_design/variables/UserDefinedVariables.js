import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';

import VariablesTable from './VariablesTable';

const UserDefinedVariables = ({variables, onAdd, onDelete, onChange, onFieldChange}) => {
  const intl = useIntl();

  const onAddUserDefinedVar = event => {
    const emptyUserDefinedVars = variables.filter(
      variable => variable.name === '' || variable.key === ''
    );

    if (emptyUserDefinedVars.length) {
      window.alert(
        intl.formatMessage({
          description: 'Warning to finish invalid user defined variable',
          defaultMessage: 'Please fill in the name of the previous variable before adding another',
        })
      );
    } else {
      onAdd(event);
    }
  };

  return (
    <>
      <VariablesTable
        variables={variables}
        editable={true}
        onDelete={onDelete}
        onChange={onChange}
        onFieldChange={onFieldChange}
      />
      <ButtonContainer onClick={onAddUserDefinedVar}>
        <FormattedMessage
          defaultMessage="Add variable"
          description="Add user defined variable button label"
        />
      </ButtonContainer>
    </>
  );
};

export default UserDefinedVariables;

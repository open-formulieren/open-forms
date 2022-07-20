import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import VariablesTable from './VariablesTable';
import ButtonContainer from '../../forms/ButtonContainer';

const UserDefinedVariables = ({variables, onAdd, onChange, onDelete}) => {
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
        onChange={onChange}
        onDelete={onDelete}
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

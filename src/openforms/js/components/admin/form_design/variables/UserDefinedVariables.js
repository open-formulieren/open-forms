import React from 'react';
import {FormattedMessage} from 'react-intl';

import VariablesTable from './VariablesTable';
import ButtonContainer from '../../forms/ButtonContainer';

const UserDefinedVariables = ({variables, onAdd, onChange, onDelete}) => {
  return (
    <>
      <VariablesTable
        variables={variables}
        editable={true}
        onChange={onChange}
        onDelete={onDelete}
      />
      <ButtonContainer onClick={onAdd}>
        <FormattedMessage
          defaultMessage="Add variable"
          description="Add user defined variable button label"
        />
      </ButtonContainer>
    </>
  );
};

export default UserDefinedVariables;

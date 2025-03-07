import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';

import RegistrationSummaryList from './registration';

const StaticData = ({onFieldChange}) => {
  const formContext = useContext(FormContext);
  const staticData = formContext.staticVariables;

  const headColumns = (
    <>
      <HeadColumn content="" />
      <HeadColumn
        content={<FormattedMessage defaultMessage="Name" description="Variable table name title" />}
      />
      <HeadColumn
        content={<FormattedMessage defaultMessage="Key" description="Variable table key title" />}
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Registration"
            description="Variable table registration title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Data type"
            description="Variable table data type title"
          />
        }
      />
    </>
  );

  return (
    <div className="variables-table">
      <ChangelistTableWrapper headColumns={headColumns} extraModifiers={['fixed']}>
        {staticData.map((item, index) => {
          return (
            <tr className={`row${(index % 2) + 1}`} key={item.key}>
              <td />
              <td>{item.name}</td>
              <td>
                <code>{item.key}</code>
              </td>
              <td>
                <RegistrationSummaryList variable={item} onFieldChange={onFieldChange} />
              </td>
              <td>{item.dataType}</td>
            </tr>
          );
        })}
      </ChangelistTableWrapper>
    </div>
  );
};

export default StaticData;

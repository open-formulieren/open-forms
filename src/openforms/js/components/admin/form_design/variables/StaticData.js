import {STATIC_VARIABLES_ENDPOINT} from '../constants';
import React, {useState} from 'react';
import useAsync from 'react-use/esm/useAsync';
import {FormattedMessage} from 'react-intl';

import {get} from 'utils/fetch';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';
import ErrorList from 'components/admin/forms/ErrorList';
import Loader from 'components/admin/Loader';

const StaticData = () => {
  const [staticData, setStaticData] = useState([]);
  const [error, setError] = useState(null);

  const {loading} = useAsync(async () => {
    const response = await get(STATIC_VARIABLES_ENDPOINT);
    if (!response.ok) {
      setError(response.data);
      return;
    }

    setStaticData(response.data);
  }, []);

  if (loading) {
    return <Loader />;
  }

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
            defaultMessage="Data type"
            description="Variable table data type title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Example initial"
            description="Variable table initial value title"
          />
        }
      />
    </>
  );

  return (
    <div className="variables-table">
      {error && <ErrorList>{error}</ErrorList>}
      <ChangelistTableWrapper headColumns={headColumns} extraModifiers={['fixed']}>
        {staticData.map((item, index) => {
          return (
            <tr className={`row${(index % 2) + 1}`}>
              <td />
              <td>{item.name}</td>
              <td>{item.key}</td>
              <td>{item.dataType}</td>
              <td>{JSON.stringify(item.initialValue)}</td>
            </tr>
          );
        })}
      </ChangelistTableWrapper>
    </div>
  );
};

export default StaticData;

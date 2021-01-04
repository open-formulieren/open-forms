import React from 'react';
import PropTypes from 'prop-types';

import Link from '@material-ui/core/Link';
import {Link as RouterLink} from 'react-router-dom';

import useAsync from 'react-use/esm/useAsync';

import { get } from './api';


const getForms = async () => {
  const formList = await get('/api/v1/forms');
  return formList;
};


const FormList = () => {
  const {loading, value, error} = useAsync(getForms, []);

  // TODO: display loader
  if (loading) return null;
  if (error) return (
    <div>Error: {JSON.stringify(error)}</div>
  );

  return (
    <ul>
    {
      value.map( form => (
        <li key={form.uuid}>
          <Link to={`/forms/${form.uuid}`}
                color="inherit"
                component={RouterLink}>
            {form.name}
          </Link>
        </li>
      ))
    }
    </ul>
  );
};

FormList.propTypes = {
};


export default FormList;

import React from 'react';

import {Link} from 'react-router-dom';
import useAsync from 'react-use/esm/useAsync';

import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import Paper from '@material-ui/core/Paper';
import CircularProgress from '@material-ui/core/CircularProgress';

import { get } from './api';


const getForms = async () => {
  const formList = await get('/api/v1/forms');
  return formList;
};


const FormList = () => {
  const {loading, value, error} = useAsync(getForms, []);

  if (loading) {
    return (<CircularProgress />);
  }

  if (error) return (
    <div>Error: {JSON.stringify(error)}</div>
  );

  return (
    <Paper>
      <List>
      {
        value.map( form => (
          <ListItem
            key={form.uuid}
            component={Link}
            to={`/forms/${form.uuid}`}
            color="inherit"
          >
            {form.name}
          </ListItem>
        ))
      }
      </List>
    </Paper>
  );
};

FormList.propTypes = {};

export default FormList;

import React from 'react';

import {Link} from 'react-router-dom';

import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import Paper from '@material-ui/core/Paper';

import AsyncLoad from './AsyncLoad';
import { get } from './api';


const getForms = async () => {
  const formList = await get('/api/v1/forms');
  return formList;
};


const FormList = () => {
  return (
    <AsyncLoad fn={getForms} render={ forms => (
      <Paper>
        <List>
        {
          forms.map( form => (
            <ListItem
              key={form.uuid}
              component={Link}
              to={`/forms/${form.uuid}/start`}
              color="inherit"
            >
              {form.name}
            </ListItem>
          ))
        }
        </List>
      </Paper>
    )} />
  );
};

FormList.propTypes = {};

export default FormList;

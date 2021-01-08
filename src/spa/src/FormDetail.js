import React from 'react';

import { useParams } from 'react-router-dom';

import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';

import AsyncLoad from './AsyncLoad';
import { get, post } from './api';


const loadForm = async (id) => {
  const form = await get(`/api/v1/forms/${id}`);
  // load the first step
  if (!form.steps.length) return {form, step: null};

  const step = await get(form.steps[0].url);
  return {form, step};
};


const useStyles = makeStyles( (theme) => ({
  code: {
    maxHeight: 400,
    overflow: 'auto',
    background: '#eee',
    padding: theme.spacing(2),
  },
  submitRow: {
    paddingTop: theme.spacing(2),
  }
}));


const FormDetail = () => {
  const { id } = useParams();
  const classes = useStyles();
  return (
    <AsyncLoad
      fn={async () => await loadForm(id).catch(console.error)}
      args={[id]}
      render={ ({form, step}) => (
        <Box component="form" onSubmit={console.log} noValidate autoComplete="off">
          <Typography variant="h2" gutterBottom> {form.name} </Typography>
          <Typography gutterBottom>{form.steps.length} step(s) total.</Typography>

          <Paper>
            <Box p={2}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    id={`form-step-data-${step.index}`}
                    label="Form step data"
                    multiline
                    rows={12}
                    value=""
                    onChange={console.log}
                    variant="outlined"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="h5" component="h3">Configuration</Typography>
                  <Typography component="pre" py={1} className={classes.code}>
                    <code>
                      {JSON.stringify(step.configuration, null, 4)}
                    </code>
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Paper>

          <Grid container justify="flex-end" className={classes.submitRow}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
            >Submit</Button>
          </Grid>

        </Box>
      )}
    />
  );
};

FormDetail.propTypes = {};


export default FormDetail;

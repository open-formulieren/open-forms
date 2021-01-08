import React, {useState} from 'react';

import { useParams, Redirect } from 'react-router-dom';

import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import Paper from '@material-ui/core/Paper';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';

import AsyncLoad from './AsyncLoad';
import { get, post } from './api';


const loadForm = async (id) => {
  const form = await get(`/api/v1/forms/${id}`);
  return form;
};


const createSubmission = async (form) => {
  const submissionResponse = await post('/api/v1/submissions', {form: form.url});
  return submissionResponse.data;
};



const useStyles = makeStyles( (theme) => ({
  submitRow: {
    paddingTop: theme.spacing(2),
    textAlign: 'center',
  }
}));


const FormDetail = () => {
  const { id } = useParams();
  const classes = useStyles();
  const [redirectTo, setRedirectTo] = useState('');

  const onSubmit = async (form, event) => {
    event.preventDefault();
    const submission = await createSubmission(form);
    const nextStepId = submission.nextStep.split('/').reverse()[0];
    setRedirectTo(`/submissions/${submission.id}/steps/${nextStepId}`);
  };

  if (redirectTo) {
    return (<Redirect push to={redirectTo} />);
  }

  return (
    <AsyncLoad
      fn={async () => await loadForm(id).catch(console.error)}
      args={[id]}
      render={ (form) => (
        <Paper>
          <Box p={2} component="form" onSubmit={onSubmit.bind(null, form)} noValidate autoComplete="off">
            <Typography variant="h2" gutterBottom> {form.name} </Typography>
            <Typography gutterBottom>{form.steps.length} step(s) total.</Typography>

            <div className={classes.submitRow}>
              <Button type="submit" variant="contained" color="primary">Start</Button>
            </div>

          </Box>
        </Paper>
      )}
    />
  );
};

FormDetail.propTypes = {};


export default FormDetail;

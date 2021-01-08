import React, {useState} from 'react';

import { useParams, Redirect } from 'react-router-dom';

import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';

import AsyncLoad from './AsyncLoad';
import { get, post, put } from './api';


const loadForm = async (id) => {
  const form = await get(`/api/v1/forms/${id}`);
  // load the first step
  if (!form.steps.length) return {form, step: null};

  const step = await get(form.steps[0].url);
  return {form, step};
};


const createSubmission = async (form) => {
  const submissionResponse = await post('/api/v1/submissions', {form: form.url});
  return submissionResponse.data;
};


const submitStepData = async (stepUrl, data) => {
  const stepDataResponse = await put(stepUrl, {data});
  return stepDataResponse.data;
};


const refreshSubmission = async (submission) => {
  const refreshed = await get(submission.url);
  return refreshed;
}


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
  const [stepData, setStepData] = useState('');
  const [submission, setSubmission] = useState(null);
  const [redirectTo, setRedirectTo] = useState('');

  const onSubmit = async (form, step, event) => {
    event.preventDefault();
    let _submission = submission;

    if (!_submission) {
      _submission = await createSubmission(form);
      setSubmission(_submission);
    }
    await submitStepData(_submission.steps[0].url, JSON.parse(stepData));
    const refreshedSubmission = await refreshSubmission(_submission);

    if (refreshedSubmission.nextStep !== null) {
      const nextStepId = refreshedSubmission.nextStep.split('/').reverse()[0];
      setRedirectTo(`/submissions/${refreshedSubmission.id}/steps/${nextStepId}`);
    } else {
      setRedirectTo(`/submissions/${refreshedSubmission.id}/complete`);
    }
  };

  if (redirectTo) {
    return (<Redirect to={redirectTo} />);
  }

  return (
    <AsyncLoad
      fn={async () => await loadForm(id).catch(console.error)}
      args={[id]}
      render={ ({form, step}) => (
        <Box component="form" onSubmit={onSubmit.bind(null, form, step)} noValidate autoComplete="off">
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
                    value={stepData}
                    onChange={ event => setStepData(event.target.value) }
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

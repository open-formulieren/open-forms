import React, {useState} from 'react';
import PropTypes from 'prop-types';

import { useParams, Redirect } from 'react-router-dom';

import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import Grid from '@material-ui/core/Grid';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import TextField from '@material-ui/core/TextField';

import AsyncLoad from './AsyncLoad';
import FormattedJson from './FormattedJson';
import SubmitRow from './SubmitRow';
import { get, put } from './api';

const loadSubmission = async (submissionId) => {
  const submission = await get(`/api/v1/submissions/${submissionId}`);
  return submission;
}

const loadSubmissionStep = async (submissionId, stepId) => {
  const url = `/api/v1/submissions/${submissionId}/steps/${stepId}`;
  const submissionStep = await get(url);
  submissionStep.url = url;  // FIXME: should be in API!
  return submissionStep;
};

const submitStepData = async (stepUrl, data) => {
  const stepDataResponse = await put(stepUrl, {data});
  return stepDataResponse.data;
};

/**
 * Display the form step form definition and handle data submission.
 * @param  {UUID} options.submissionId The ID of the submission currently being processed.
 * @param  {Object} options.step       The SubmissionStep instance for the particular form step.
 * @return {JSX}                       Render the form and redirect after valid submission.
 */
const FormStep = ({ submissionId, step }) => {
  const [stepData, setStepData] = useState(step.data ? JSON.stringify(step.data) : '');
  const [redirectTo, setRedirectTo] = useState('');

  const onSubmit = async (event) => {
    event.preventDefault();
    await submitStepData(step.url, JSON.parse(stepData));
    const submission = await loadSubmission(submissionId);

    if (submission.nextStep !== null) {
      const nextStepId = submission.nextStep.split('/').reverse()[0];
      setRedirectTo(`/submissions/${submission.id}/steps/${nextStepId}`);
    } else {
      setRedirectTo(`/submissions/${submission.id}/complete`);
    }
  };

  if (redirectTo) {
    return (<Redirect push to={redirectTo} />);
  }

  return (
    <Paper>
      <Box p={2} component="form" onSubmit={onSubmit} noValidate autoComplete="off">
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              id={`form-step-data-${step.formStep.index}`}
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
            <FormattedJson data={step.formStep.configuration} />
          </Grid>
        </Grid>

        <SubmitRow>
          <Button type="submit" variant="contained" color="primary">Submit</Button>
        </SubmitRow>
      </Box>
    </Paper>
  );
};

FormStep.propTypes = {
  submissionId: PropTypes.string.isRequired,
  step: PropTypes.object.isRequired,
};


/**
 * Load the form step data and render the form step component as a result.
 * @return {JSX} Loader spinner until the data has been fetched
 */
const FormStepContainer = () => {
    const { submissionId, stepId } = useParams();
    return (
      <AsyncLoad
        fn={async () => await loadSubmissionStep(submissionId, stepId).catch(console.error)}
        args={[submissionId, stepId]}
        render={ (submissionStep) => (<FormStep step={submissionStep} submissionId={submissionId} />) }
      />
    );
};

FormStepContainer.propTypes = {};

export default FormStepContainer;

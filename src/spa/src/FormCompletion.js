import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import zip from 'lodash/zip';

import { useParams, Redirect } from 'react-router-dom';

import Button from '@material-ui/core/Button';
import Box from '@material-ui/core/Box';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import DoneIcon from '@material-ui/icons/Done';
import ClearIcon from '@material-ui/icons/Clear';

import AsyncLoad from './AsyncLoad';
import FormattedJson from './FormattedJson';
import SubmitRow from './SubmitRow';
import { get, post } from './api';
import { SnackbarContext } from './Context';

const loadSubmissionOverview = async (submissionId) => {
  const submission = await get(`/api/v1/submissions/${submissionId}`);

  // get the step data
  const promises = submission.steps.map(step => get(step.url));
  const stepsData = await Promise.all(promises);

  const overview =
    zip(submission.steps, stepsData)
    .map(([meta, stepData]) => ({
      name: meta.name,
      available: meta.available,
      completed: meta.completed,
      optional: meta.optional,
      data: stepData.data,
    }) );
  return overview;
};

const completeSubmission = async (submissionId) => {
    await post(`/api/v1/submissions/${submissionId}/_complete`);
};

const StepSummary = ({ name, available, completed, optional, data }) => {
  return (
    <Paper>
      <Box p={2}>
        <Typography variant="h5" component="h3" gutterBottom>{name}</Typography>
        { completed ? <DoneIcon title="Completed" /> : <ClearIcon title="Not completed yet" /> }
        <FormattedJson data={data} />
      </Box>
    </Paper>
  );
};

StepSummary.propTypes = {
  name: PropTypes.string.isRequired,
  available: PropTypes.bool.isRequired,
  completed: PropTypes.bool.isRequired,
  optional: PropTypes.bool.isRequired,
  data: PropTypes.object,
};

const FormCompletion = ({submissionId, steps=[]}) => {
  const [completed, setCompleted] = useState(false);
  const setSnackbarState = useContext(SnackbarContext)[1];

  const onSubmit = async (event) => {
    event.preventDefault();

    try {
      await completeSubmission(submissionId);
      setSnackbarState({
        open: true,
        onClose: () => setSnackbarState(null),
      });
      setCompleted(true);
    } catch (error) {
      console.error(error);
    }
  };

  if (completed) {
    return (<Redirect push to="/" />);
  }

  return (
    <Box component="form" onSubmit={onSubmit} noValidate autoComplete="off">
      <Typography variant="h4" component="h2" gutterBottom>Summary</Typography>
      {steps.map( (stepData, index) => (
          <StepSummary {...stepData} key={index} />
        ) )}
      <SubmitRow>
        <Button type="submit" variant="contained" color="primary">Confirm</Button>
      </SubmitRow>
    </Box>
  );
};

FormCompletion.propTypes = {
  submissionId: PropTypes.string.isRequired,
  steps: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    available: PropTypes.bool.isRequired,
    completed: PropTypes.bool.isRequired,
    optional: PropTypes.bool.isRequired,
    data: PropTypes.object,
  })).isRequired,
};

const FormCompletionContainer = () => {
    const { submissionId } = useParams();
    return (
      <AsyncLoad
        fn={async () => await loadSubmissionOverview(submissionId).catch(console.error)}
        args={[submissionId]}
        render={ (steps) => (<FormCompletion steps={steps} submissionId={submissionId} />) }
      />
    );
};

FormCompletionContainer.propTypes = {};


export default FormCompletionContainer;

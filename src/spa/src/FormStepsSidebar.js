import React from 'react';
import PropTypes from 'prop-types';

import {Link} from 'react-router-dom';

import Stepper from '@material-ui/core/Stepper';
import Step from '@material-ui/core/Step';
import StepButton from '@material-ui/core/StepButton';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';


const FormStepsSidebar = ({ steps, activeStep, submissionId }) => {
  return (
    <Paper variant="outlined">
      <Stepper orientation="vertical" nonLinear activeStep={activeStep}>
        {
          steps.map( step => {
            const optional = step.optional ? (<Typography variant="caption">Optional</Typography>) : null;
            return (
              <Step
                key={step.id}
                completed={step.completed}
                disabled={!step.available}
              >
                <StepButton
                  optional={optional}
                  component={Link}
                  to={`/submissions/${submissionId}/steps/${step.id}`}
                >
                  {step.name}
                </StepButton>
              </Step>
            );
          })
        }
      </Stepper>
    </Paper>
  );
};


FormStepsSidebar.propTypes = {
    steps: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      available: PropTypes.bool.isRequired,
      completed: PropTypes.bool.isRequired,
      optional: PropTypes.bool.isRequired,
    })).isRequired,
    activeStep: PropTypes.number.isRequired,
    submissionId: PropTypes.string.isRequired,
};


export default FormStepsSidebar;

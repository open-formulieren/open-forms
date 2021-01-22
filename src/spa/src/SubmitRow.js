import React from 'react';
import PropTypes from 'prop-types';

import Grid from '@material-ui/core/Grid';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles( (theme) => ({
  submitRow: {
    paddingTop: theme.spacing(2),
  }
}));

const SubmitRow = ({ children }) => {
  const classes = useStyles();
  return (
    <Grid container space={2} justify="flex-end" className={classes.submitRow}>
      {children}
    </Grid>
  );
};

SubmitRow.propTypes = {
    children: PropTypes.node.isRequired,
};

export default SubmitRow;

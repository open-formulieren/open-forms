import React from 'react';
import PropTypes from 'prop-types';

import { makeStyles } from '@material-ui/core/styles';
import Typography from '@material-ui/core/Typography';

const useStyles = makeStyles( (theme) => ({
  code: {
    maxHeight: 400,
    overflow: 'auto',
    background: '#eee',
    padding: theme.spacing(2),
  },
}));

const FormattedJson = ({ data }) => {
  const classes = useStyles();
  return (
    <Typography component="pre" py={1} className={classes.code}>
      <code>
        {JSON.stringify(data, null, 4)}
      </code>
    </Typography>
  );
};

FormattedJson.propTypes = {
    data: PropTypes.object,
};


export default FormattedJson;

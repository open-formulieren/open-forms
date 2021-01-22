import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import MuiSnackbar from '@material-ui/core/Snackbar';
import IconButton from '@material-ui/core/IconButton';
import CloseIcon from '@material-ui/icons/Close';

import { SnackbarContext } from './Context';


const Snackbar = () => {
  const [snackbarState, ...rest] = useContext(SnackbarContext);
  if (snackbarState == null) {
    return null;
  }

  const {open, onClose} = snackbarState;

  return (
    <MuiSnackbar
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'left',
      }}
      open={open}
      autoHideDuration={3000}
      onClose={onClose}
      message="Form submission completed"
      action={
        <React.Fragment>
          <IconButton size="small" aria-label="close" color="inherit" onClick={onClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </React.Fragment>
      }
    />
  );
};

Snackbar.propTypes = {};


export default Snackbar;

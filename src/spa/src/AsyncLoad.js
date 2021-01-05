import React from 'react';
import PropTypes from 'prop-types';

import useAsync from 'react-use/esm/useAsync';
import CircularProgress from '@material-ui/core/CircularProgress';


const AsyncLoad = ({ fn, args=[], render }) => {
    const {loading, value, error} = useAsync(fn, args);
    if (loading) {
      return (<CircularProgress />);
    }
    if (error) return (
      <div>Error: {JSON.stringify(error)}</div>
    );
    return render(value);
};

AsyncLoad.propTypes = {
    fn: PropTypes.func.isRequired,
    args: PropTypes.array,
    render: PropTypes.func.isRequired,
};


export default AsyncLoad;

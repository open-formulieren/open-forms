import PropTypes from 'prop-types';
import React from 'react';

/**
 * Display a loader animation.
 *
 * Taken and adapted from https://codepen.io/joshuaward/pen/XejbZv
 * @return {JSX}
 */
const Loader = () => {
  return (
    <div className="box-loader-container">
      <div className="box-loader">
        <div />
        <div />
        <div />
      </div>
    </div>
  );
};

Loader.propTypes = {};

export default Loader;

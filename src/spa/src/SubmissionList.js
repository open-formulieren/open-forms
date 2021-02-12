import React from 'react';
import PropTypes from 'prop-types';

import AsyncLoad from './AsyncLoad';
import { get } from './api';


const getSubmissions = async () => {
  const results = await get('/api/v1/submissions');
  return results;
};


const SubmissionList = ({ submissions=[] }) => {
    console.log(submissions);
    return (
      null
    );
};

SubmissionList.propTypes = {
    submissions: PropTypes.arrayOf(PropTypes.object).isRequired,
};


const SubmissionListContainer = () => {
  return (
    <AsyncLoad
      fn={getSubmissions}
      render={ (submissions) => <SubmissionList submissions={submissions} /> }
    />
  );
};

SubmissionListContainer.propTypes = {};


export default SubmissionListContainer;

import React from 'react';
import PropTypes from 'prop-types';

import { useParams } from 'react-router-dom';


const FormDetail = () => {
  const { id } = useParams();
  return (
    <article className="form-detail">
      Form: {id}
    </article>
  );
};

FormDetail.propTypes = {
};


export default FormDetail;

import React from 'react';
import PropTypes from 'prop-types';


const Fieldset = ({ title='', children, ...extra }) => {
    const titleNode = title ? <h2>{title}</h2> : null;
    return (
        <fieldset className="module aligned" {...extra}>
            {titleNode}
            {children}
        </fieldset>
    );
};

Fieldset.propTypes = {
    title: PropTypes.node,
    children: PropTypes.node,
};


export default Fieldset;

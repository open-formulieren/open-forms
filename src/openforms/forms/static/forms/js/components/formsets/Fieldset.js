import React from 'react';
import PropTypes from 'prop-types';


const Fieldset = ({ title='', children }) => {
    const titleNode = title ? <h2>{title}</h2> : null;
    return (
        <fieldset className="module aligned">
            {titleNode}
            {children}
        </fieldset>
    );
};

Fieldset.propTypes = {
    title: PropTypes.string,
    children: PropTypes.node,
};


export default Fieldset;

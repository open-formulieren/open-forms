import React from 'react';
import PropTypes from 'prop-types';


const Fieldset = ({ title='', children, extraClassName, ...extra }) => {
    const titleNode = title ? <h2>{title}</h2> : null;
    const className = `module aligned ${extraClassName || ''}`;

    return (
        <fieldset className={className} {...extra}>
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

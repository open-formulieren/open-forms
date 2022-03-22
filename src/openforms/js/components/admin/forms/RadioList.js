import React from 'react';
import PropTypes from 'prop-types';

const RadioList = ({ children }) => (
    <ul className="radiolist">
        {React.Children.map(children, (child) => (
            <li key={child.key}>
                {child}
            </li>
        ))}
    </ul>
);

RadioList.propTypes = {
    children: PropTypes.node.isRequired,
};

export default RadioList;

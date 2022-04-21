import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import ErrorList from '../../forms/ErrorList';


const DSLEditorNode = ({ errors, children }) => (
    <div className={classNames('dsl-editor__node', {'dsl-editor__node--errors': !!errors})}>
        <ErrorList classNamePrefix="logic-action">{errors}</ErrorList>
        {children}
    </div>
);

DSLEditorNode.propTypes = {
    children: PropTypes.oneOfType([
      PropTypes.arrayOf(PropTypes.node),
      PropTypes.node,
    ]),
    errors: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ])
};

export default DSLEditorNode;

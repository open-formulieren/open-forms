import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';

import ErrorList from 'components/admin/forms/ErrorList';

const DSLEditorNode = ({errors, flexGrow, children}) => (
  <div
    className={classNames('dsl-editor__node', {
      'dsl-editor__node--errors': !!errors,
      'dsl-editor__node--flex-grow-1': !!flexGrow,
    })}
  >
    <ErrorList classNamePrefix="logic-action">{errors}</ErrorList>
    {children}
  </div>
);

DSLEditorNode.propTypes = {
  children: PropTypes.node,
  flexGrow: PropTypes.bool,
  errors: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.string), PropTypes.string]),
};

export default DSLEditorNode;

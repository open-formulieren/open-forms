import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';

import ErrorList from 'components/admin/forms/ErrorList';

const DSLEditorNode = ({errors, children}) => (
  <div className={classNames('dsl-editor__node', {'dsl-editor__node--errors': !!errors?.length})}>
    <ErrorList classNamePrefix="logic-action">{errors}</ErrorList>
    {children}
  </div>
);

DSLEditorNode.propTypes = {
  children: PropTypes.node,
  errors: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.string), PropTypes.string]),
};

export default DSLEditorNode;

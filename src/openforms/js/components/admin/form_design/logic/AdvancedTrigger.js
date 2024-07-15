import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';

import JsonWidget from 'components/admin/forms/JsonWidget';
import jsonPropTypeValidator from 'utils/JsonPropTypeValidator';

const AdvancedTrigger = ({expandExpression, name, logic, onChange, error}) => {
  return (
    <div className="logic-trigger">
      <div
        className={classNames('logic-trigger__json-editor', {
          'logic-trigger__json-editor--error': error,
        })}
      >
        <JsonWidget name={name} logic={logic} onChange={onChange} isExpanded={expandExpression} />
        {error ? <div className="logic-trigger__error">{error}</div> : null}
      </div>
    </div>
  );
};

AdvancedTrigger.propTypes = {
  expandExpression: PropTypes.bool.isRequired,
  name: PropTypes.string.isRequired,
  logic: jsonPropTypeValidator,
  onChange: PropTypes.func.isRequired,
  error: PropTypes.string,
};

export default AdvancedTrigger;

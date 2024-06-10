import classNames from 'classnames';
import jsonLogic from 'json-logic-js';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useIntl} from 'react-intl';

import jsonPropTypeValidator from 'utils/JsonPropTypeValidator';

import {TextArea} from './Inputs';

// dump JSON in a readable form
const jsonFormat = value => {
  return JSON.stringify(value, null, 2);
};

const isJsonLogic = jsonExpression => {
  // jsonLogic accepts primitives
  if (
    jsonExpression == null || // typeof null -> 'object'
    typeof jsonExpression === 'string' ||
    typeof jsonExpression === 'boolean' ||
    typeof jsonExpression === 'number'
  ) {
    return true;
  }

  if (Array.isArray(jsonExpression)) {
    for (const item of jsonExpression) {
      const isValid = isJsonLogic(item);
      if (!isValid) return false;
    }
    return true;
  }

  return jsonLogic.is_logic(jsonExpression);
};

const JsonWidget = ({name, logic, onChange, cols = 60, isExpanded = true}) => {
  const intl = useIntl();
  const [jsonError, setJsonError] = useState('');
  const [editorValue, setEditorValue] = useState(jsonFormat(logic));

  useEffect(() => {
    setEditorValue(jsonFormat(logic));
  }, [logic]);

  const invalidSyntaxMessage = intl.formatMessage({
    description: 'Advanced logic rule invalid json message',
    defaultMessage: 'Invalid JSON syntax',
  });
  const invalidLogicMessage = intl.formatMessage({
    description: 'Advanced logic rule invalid JSON-logic message',
    defaultMessage: 'Invalid JSON logic expression',
  });

  const onJsonChange = event => {
    const newValue = event.target.value;
    setEditorValue(newValue);
    setJsonError('');

    let updatedJson;

    try {
      updatedJson = JSON.parse(newValue);
    } catch (error) {
      if (error instanceof SyntaxError) {
        setJsonError(invalidSyntaxMessage);
        return;
      } else {
        throw error;
      }
    }

    if (!isJsonLogic(updatedJson)) {
      setJsonError(invalidLogicMessage);
      return;
    }

    const fakeEvent = {target: {name: name, value: updatedJson}};
    onChange(fakeEvent);
  };

  return (
    <div className={classNames('json-widget', {'json-widget--collapsed': !isExpanded})}>
      <div className="json-widget__input">
        <TextArea
          name={name}
          id={`id_${name}`}
          value={editorValue}
          onChange={onJsonChange}
          cols={cols}
          rows={isExpanded ? Math.min(20, editorValue.split('\n').length) : 1}
        />
      </div>
      {jsonError.length ? <div className="json-widget__error">{jsonError}</div> : null}
    </div>
  );
};

JsonWidget.propTypes = {
  name: PropTypes.string.isRequired,
  logic: jsonPropTypeValidator,
  onChange: PropTypes.func.isRequired,
  cols: PropTypes.number,
  isExpanded: PropTypes.bool,
};

export default JsonWidget;

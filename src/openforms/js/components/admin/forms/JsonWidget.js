import {JSONEditor} from '@open-formulieren/monaco-json-editor';
import classNames from 'classnames';
import jsonLogic from 'json-logic-js';
import {isEqual} from 'lodash';
import PropTypes from 'prop-types';
import {useEffect, useRef, useState} from 'react';
import {useIntl} from 'react-intl';
import {useGlobalState} from 'state-pool';

import jsonPropTypeValidator from 'utils/JsonPropTypeValidator';
import {currentTheme} from 'utils/theme';

const MIN_LINES = 3;

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

const JsonWidget = ({
  name,
  logic,
  onChange,
  cols = 60,
  maxRows = 20,
  isExpanded = true,
  testid,
}) => {
  const intl = useIntl();
  const [theme] = useGlobalState(currentTheme);
  const [jsonError, setJsonError] = useState('');
  const [numRows, setNumRows] = useState(MIN_LINES);

  const initialLogicRef = useRef(logic);

  useEffect(() => {
    if (isEqual(logic, initialLogicRef.current)) return;
    console.debug(`external 'logic' prop changes are currently not handled!`);
  }, [logic]);

  const invalidLogicMessage = intl.formatMessage({
    description: 'Advanced logic rule invalid JSON-logic message',
    defaultMessage: 'Invalid JSON logic expression',
  });

  const onJsonChange = value => {
    setJsonError('');

    if (!isJsonLogic(value)) {
      setJsonError(invalidLogicMessage);
      return;
    }

    const fakeEvent = {target: {name: name, value}};
    onChange(fakeEvent);
  };

  return (
    <div
      className={classNames('json-widget', {'json-widget--collapsed': !isExpanded})}
      data-testid={testid}
    >
      {isExpanded && (
        <div
          className="json-widget__input json-widget__input--resizable"
          style={{
            '--of-json-widget-cols': cols,
            '--of-json-widget-rows': Math.min(maxRows, Math.max(MIN_LINES, numRows)),
          }}
        >
          <JSONEditor
            defaultValue={JSON.stringify(logic, null, 2)}
            onChange={onJsonChange}
            lineCountCallback={(numLines = 1) => setNumRows(numLines)}
            theme={theme}
            automaticLayout={true}
          />
        </div>
      )}
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
  testid: PropTypes.string,
};

export default JsonWidget;

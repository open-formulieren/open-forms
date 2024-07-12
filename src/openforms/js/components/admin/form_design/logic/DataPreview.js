import {JSONEditor} from '@open-formulieren/monaco-json-editor';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useGlobalState} from 'state-pool';

import {currentTheme} from 'utils/theme';

const DataPreview = ({data, maxRows = 20}) => {
  const [numRows, setNumRows] = useState(1);
  const [theme] = useGlobalState(currentTheme);

  return (
    <div
      className="json-data-preview"
      style={{
        '--of-json-widget-rows': Math.min(maxRows, numRows),
        '--of-json-widget-cols': 40,
      }}
    >
      <JSONEditor
        value={data}
        theme={theme}
        readOnly
        showLines={false}
        lineCountCallback={(numLines = 1) => setNumRows(numLines)}
      />
    </div>
  );
};

DataPreview.propTypes = {
  data: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.bool,
    PropTypes.string,
    PropTypes.number,
    PropTypes.array,
  ]),
  maxRows: PropTypes.number,
};

export default DataPreview;

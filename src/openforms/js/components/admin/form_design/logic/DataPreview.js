import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';


const DataPreview = ({ data }) => {
    const [visible, setVisible] = useState(false);
    return (
        <div className="json-data-preview">
            <a href="#" onClick={ e => e.preventDefault() || setVisible(!visible) } className="json-data-preview__toggle">
                <FormattedMessage
                    description="JSON data preview visibility toggle"
                    defaultMessage="Toggle DSL preview"
                />
            </a>
            {
                visible
                ? (<pre className="json-data-preview__preview">{JSON.stringify(data, null, 2)}</pre>)
                : null
            }
        </div>
    );
};

DataPreview.propTypes = {
    data: PropTypes.object,
};


export default DataPreview;

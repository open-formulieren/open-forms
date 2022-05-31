import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

const FormObjectTools = ({isLoading, formUrl, historyUrl}) => {
  /* TODO The buttons are disabled if the form page is still loading. Interrupting the fetch of form data
    raises an error which is displayed as 'The form is invalid. Please correct the errors below.'.
     */
  return (
    <div className="form-object-tools">
      <ul
        className={`object-tools form-object-tools__list ${
          isLoading ? 'form-object-tools__loading' : ''
        }`}
      >
        {formUrl ? (
          <li>
            <a target="_blank" href={formUrl} className="historylink">
              <FormattedMessage defaultMessage="Show form" description="Show form button" />
            </a>
          </li>
        ) : null}
        <li>
          <a href={historyUrl} className="historylink">
            <FormattedMessage defaultMessage="History" description="History link button" />
          </a>
        </li>
      </ul>
    </div>
  );
};

FormObjectTools.propTypes = {
  isLoading: PropTypes.bool.isRequired,
  historyUrl: PropTypes.string.isRequired,
  formUrl: PropTypes.string.isRequired,
};

export default FormObjectTools;

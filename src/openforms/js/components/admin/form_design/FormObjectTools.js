import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

const FormObjectTools = ({isLoading, isActive, formUrl, historyUrl, formJsonSchemaUrl}) => {
  /* TODO The buttons are disabled if the form page is still loading. Interrupting the fetch of form data
    raises an error which is displayed as 'The form is invalid. Please correct the errors below.'.
     */
  const intl = useIntl();
  const showFormStyling = !isActive
    ? {cursor: 'not-allowed', textDecoration: 'none', background: '#555'}
    : {};

  return (
    <div className="form-object-tools">
      <ul
        className={`object-tools form-object-tools__list ${
          isLoading ? 'form-object-tools__loading' : ''
        }`}
      >
        <li>
          <a href={formJsonSchemaUrl} target="_blank" className="historylink">
            <FormattedMessage
              defaultMessage="Generate JSON schema"
              description="From JSON schema button"
            />
          </a>
        </li>
        {formUrl ? (
          <li>
            <a
              title={
                !isActive
                  ? intl.formatMessage({
                      defaultMessage: 'The form is not active',
                      description: 'Show form button disabled title',
                    })
                  : undefined
              }
              target={isActive ? '_blank' : '_self'}
              href={isActive ? formUrl : '#'}
              aria-disabled={!isActive ? true : undefined}
              style={showFormStyling}
              className="historylink"
            >
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
  isActive: PropTypes.bool.isRequired,
  historyUrl: PropTypes.string.isRequired,
  formUrl: PropTypes.string.isRequired,
  formJsonSchemaUrl: PropTypes.string.isRequired,
};

export default FormObjectTools;

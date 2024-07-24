import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FAIcon} from 'components/admin/icons';

const LogicTypeSelection = ({onChange, onCancel}) => {
  const intl = useIntl();
  return (
    <div className="logic-type-selection">
      <label className="logic-type-selection__label">
        <FormattedMessage
          description="Logic type selection label"
          defaultMessage="Please select the logic type:"
        />
      </label>

      <div className="tiles tiles--horizontal">
        <button
          type="button"
          className="tiles__tile tiles__tile--small"
          onClick={() => onChange('simple')}
        >
          <span>
            <FormattedMessage description="Simple logic type" defaultMessage="Simple" />
            <br />
            <FAIcon
              icon="circle-info"
              title={intl.formatMessage({
                description: 'Simple logic type info text',
                defaultMessage:
                  'Select components and conditions using drop-downs to build a JsonLogic expression.',
              })}
            />
          </span>
        </button>

        <span className="tiles__separator">&bull;</span>

        <button
          type="button"
          className="tiles__tile tiles__tile--small"
          onClick={() => onChange('advanced')}
        >
          <span>
            <FormattedMessage description="Advanced logic type" defaultMessage="Advanced" />
            <br />
            <FAIcon
              icon="circle-info"
              title={intl.formatMessage({
                description: 'Advanced logic type info text',
                defaultMessage: 'Build a JsonLogic expression using raw JSON.',
              })}
            />
          </span>
        </button>
      </div>

      <a
        href="#"
        className="logic-type-selection__cancel"
        onClick={e => {
          e.preventDefault();
          onCancel();
        }}
        title={intl.formatMessage({
          description: 'Cancel link help',
          defaultMessage: 'Cancel rule creation',
        })}
      >
        <FormattedMessage description="Cancel link" defaultMessage="Cancel" />
      </a>
    </div>
  );
};

LogicTypeSelection.propTypes = {
  onChange: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default LogicTypeSelection;

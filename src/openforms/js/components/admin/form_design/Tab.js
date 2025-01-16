import PropTypes from 'prop-types';
import React from 'react';
import {useIntl} from 'react-intl';
import {Tab as ReactTab} from 'react-tabs';

import {ErrorIcon} from 'components/admin/icons';

const Tab = ({hasErrors = false, children, ...props}) => {
  const intl = useIntl();
  const customProps = {
    className: ['react-tabs__tab', {'react-tabs__tab--has-errors': hasErrors}],
  };
  const allProps = {...props, ...customProps};
  const title = intl.formatMessage({
    defaultMessage: 'There are validation errors',
    description: 'Tab validation errors icon title',
  });
  return (
    <ReactTab {...allProps}>
      {children}
      {hasErrors ? <ErrorIcon extraClassname="react-tabs__error-badge" text={title} /> : null}
    </ReactTab>
  );
};
Tab.tabsRole = 'Tab';

Tab.propTypes = {
  hasErrors: PropTypes.bool,
};

export default Tab;

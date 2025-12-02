import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import MessageList from '../MessageList';

const MultipleProfileComponentsWarning = ({profileComponents}) => {
  if (profileComponents.length <= 1) return null;

  const warning = {
    level: 'warning',
    message: (
      <FormattedMessage
        description="Too many profile components"
        defaultMessage="There are multiple profile components specified in this form. At most one should be present."
      />
    ),
  };

  return <MessageList messages={[warning]} />;
};

MultipleProfileComponentsWarning.propTypes = {
  profileComponents: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default MultipleProfileComponentsWarning;

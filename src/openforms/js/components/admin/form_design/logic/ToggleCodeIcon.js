import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';

import {FAIcon} from 'components/admin/icons';

const ToggleCodeIcon = ({viewMode, setViewMode}) => {
  const intl = useIntl();
  const title = intl.formatMessage(
    {
      description: 'Toggle icon for JSON logic presentation mode.',
      defaultMessage:
        '{viewMode, select, ui {Show JSON definition} json {Show editor} other {UNKNOWN}}',
    },
    {viewMode: viewMode}
  );

  return (
    <FAIcon
      icon="code"
      extraClassname="actions__action icon"
      title={title}
      aria-label={title}
      onClick={() => setViewMode(viewMode === 'ui' ? 'json' : 'ui')}
    />
  );
};

ToggleCodeIcon.propTypes = {
  viewMode: PropTypes.oneOf(['ui', 'json']),
  setViewMode: PropTypes.func,
};

export default ToggleCodeIcon;

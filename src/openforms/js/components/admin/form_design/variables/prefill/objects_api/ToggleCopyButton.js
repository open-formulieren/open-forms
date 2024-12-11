import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';

import useStatus from './useStatus';

const ToggleCopyButton = () => {
  const {registrationBackends = []} = useContext(FormContext);
  const {toggleShowCopyButton} = useStatus();
  const backends = registrationBackends.filter(elem => elem.backend === 'objects_api');
  // don't render a toggle if there's nothing to copy from
  if (!backends.length) return null;

  return (
    <a
      href="#"
      onClick={event => {
        event.preventDefault();
        toggleShowCopyButton();
      }}
    >
      <FormattedMessage
        description={'Objects API prefill options: link to show copy from registration button'}
        defaultMessage={'Copy configuration from registration'}
      />
    </a>
  );
};

ToggleCopyButton.propTypes = {};

export default ToggleCopyButton;

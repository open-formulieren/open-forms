import {FormattedMessage} from 'react-intl';

const ToggleCopyButton = ({handleToggle}) => {
  return (
    <a href="#" onClick={handleToggle}>
      <FormattedMessage
        description={'Objects API prefill options: link to show copy from registration button'}
        defaultMessage={'Copy configuration from registration'}
      />
    </a>
  );
};

export default ToggleCopyButton;

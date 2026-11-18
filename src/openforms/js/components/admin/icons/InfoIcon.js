import classNames from 'classnames';
import PropTypes from 'prop-types';

import FAIcon from './FAIcon';

const InfoIcon = ({asLead = false, text}) => (
  <FAIcon
    icon="circle-info"
    extraClassname={classNames('icon', 'icon--info', 'icon--no-pointer', {
      'icon--as-lead': asLead,
    })}
    accessibleLabel={text}
  />
);

InfoIcon.propTypes = {
  asLead: PropTypes.bool,
  text: PropTypes.string,
};

export default InfoIcon;

import '@utrecht/components/alert';
import PropTypes from 'prop-types';

const Alert = ({children, type}) => {
  return (
    <div className={`alert alert-${type}`} role="alert">
      {children}
    </div>
  );
};

Alert.propTypes = {
  type: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

export default Alert;

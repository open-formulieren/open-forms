import PropTypes from 'prop-types';

const Variable = PropTypes.shape({
  form: PropTypes.string,
  formDefinition: PropTypes.string,
  name: PropTypes.string,
  key: PropTypes.string.isRequired,
  source: PropTypes.string,
  prefillPlugin: PropTypes.string,
  prefillAttribute: PropTypes.string,
  dataType: PropTypes.string,
  dataFormat: PropTypes.string,
  isSensitiveData: PropTypes.bool,
  initialValue: PropTypes.oneOfType([
    PropTypes.array,
    PropTypes.bool,
    PropTypes.number,
    PropTypes.object,
    PropTypes.string,
  ]),
  errors: PropTypes.object,
  showInEmail: PropTypes.bool,
  showInPdf: PropTypes.bool,
  showInSummary: PropTypes.bool,
});

export default Variable;

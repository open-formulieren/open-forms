import PropTypes from 'prop-types';

const FormStep = PropTypes.shape({
  configuration: PropTypes.object,
  formDefinition: PropTypes.string,
  index: PropTypes.number,
  name: PropTypes.string,
  internalName: PropTypes.string,
  slug: PropTypes.string,
  isApplicable: PropTypes.bool,
  loginRequired: PropTypes.bool,
  isReusable: PropTypes.bool,
  url: PropTypes.string,
  isNew: PropTypes.bool,
  validationErrors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  translations: PropTypes.objectOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      saveText: PropTypes.string.isRequired,
      previousText: PropTypes.string.isRequired,
      nextText: PropTypes.string.isRequired,
    })
  ),
});

export default FormStep;

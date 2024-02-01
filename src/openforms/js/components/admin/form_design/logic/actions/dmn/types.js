import PropTypes from 'prop-types';

const inputValuesType = PropTypes.shape({
  pluginId: PropTypes.string,
  decisionDefinitionId: PropTypes.string,
  decisionDefinitionVersion: PropTypes.string,
  inputMapping: PropTypes.arrayOf(
    PropTypes.shape({
      formVar: PropTypes.string,
      dmnVar: PropTypes.string,
    })
  ),
  outputMapping: PropTypes.arrayOf(
    PropTypes.shape({
      formVar: PropTypes.string,
      dmnVar: PropTypes.string,
    })
  ),
});

export {inputValuesType};

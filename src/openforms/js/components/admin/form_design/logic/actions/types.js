import PropTypes from 'prop-types';

const jsonLogicVar = PropTypes.shape({
  var: PropTypes.string,
});

const Action = PropTypes.shape({
  action: PropTypes.shape({
    property: PropTypes.shape({
      type: PropTypes.string,
      value: PropTypes.string,
    }),
    type: PropTypes.string,
    state: PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number,
      PropTypes.bool,
      PropTypes.object,
    ]),
    source: PropTypes.string,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number, jsonLogicVar]),
  }),
  component: PropTypes.string,
  formStep: PropTypes.string,
  formStepUuid: PropTypes.string,
});

const ActionConfigMappingError = PropTypes.arrayOf(
  PropTypes.shape({
    dmnVariable: PropTypes.string,
    formVariable: PropTypes.string,
  })
);

const ActionConfigError = PropTypes.oneOfType([
  PropTypes.string,
  PropTypes.shape({
    inputMapping: ActionConfigMappingError,
    outputMapping: ActionConfigMappingError,
  }),
]);

const ActionError = PropTypes.shape({
  action: PropTypes.shape({
    state: PropTypes.string,
    type: PropTypes.string,
    property: PropTypes.shape({
      type: PropTypes.string,
      value: PropTypes.string,
    }),
    value: PropTypes.string,
    config: ActionConfigError,
  }),
  component: PropTypes.string,
  formStep: PropTypes.string,
  formStepUuid: PropTypes.string,
});

export {jsonLogicVar, Action, ActionError, ActionConfigError};

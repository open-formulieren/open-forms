import PropTypes from 'prop-types';

const jsonLogicVar = PropTypes.shape({
    var: PropTypes.string
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
        value: PropTypes.oneOfType([
            PropTypes.string,
            PropTypes.number,
            jsonLogicVar,
        ])
    }),
    component: PropTypes.string,
    formStep: PropTypes.string,
});

const ActionError = PropTypes.shape({
    action: PropTypes.shape({
        state: PropTypes.string,
        type: PropTypes.string,
        property: PropTypes.shape({
            type: PropTypes.string,
            value: PropTypes.string,
        }),
        value: PropTypes.string,
    }),
    component: PropTypes.string,
    formStep: PropTypes.string,
});

export {jsonLogicVar, Action, ActionError};

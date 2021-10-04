import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import {useIntl, FormattedMessage} from 'react-intl';

import FAIcon from '../FAIcon';
import DeleteIcon from '../DeleteIcon';


const FormStepNavItem = ({ name, active=false, onActivate, onReorder, onDelete, hasErrors=false }) => {
    const intl = useIntl();
    const className = classNames(
        'list__item',
        'list__item--with-actions',
        {'list__item--active': active},
    );

    const confirmDeleteMessage = intl.formatMessage({
        description: 'Step delete confirmation',
        defaultMessage: 'Are you sure you want to delete the step {step}?'
    }, {
        step: name,
    });

    const iconTitle = intl.formatMessage({
        description: 'Step validation errors icon title',
        defaultMessage: 'There are validation errors',
    });

    return (
        <li className={className}>
            <div className="actions actions--vertical">
                <FAIcon
                    icon="angle-up"
                    title={intl.formatMessage({description: 'Move up icon title', defaultMessage: 'Move up'})}
                    extraClassname="fa-lg actions__action"
                    onClick={ () => onReorder('up') }
                />
                <FAIcon
                    icon="angle-down"
                    title={intl.formatMessage({description: 'Move down icon title', defaultMessage: 'Move down'})}
                    extraClassname="fa-lg actions__action"
                    onClick={ () => onReorder('down') }
                />
            </div>
            <button type="button" onClick={onActivate} className="button button--plain">
                { hasErrors
                    ? (<FAIcon icon="exclamation-circle" title={iconTitle} extraClassname="icon icon--danger" />)
                    : null
                }
                {name}
            </button>
            <div className="actions">
                <DeleteIcon
                    message={confirmDeleteMessage}
                    onConfirm={onDelete}
                />
            </div>
        </li>
    );
};

FormStepNavItem.propTypes = {
    name: PropTypes.node.isRequired,
    active: PropTypes.bool.isRequired,
    onActivate: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    hasErrors: PropTypes.bool,
};


const FormStepsNav = ({ steps=[], active=null, onActivateStep, onReorder, onDelete, onAdd }) => {
    const intl = useIntl();

    const onStepAdd = (event) => {
        onAdd(event);
        onActivateStep(steps.length);
    };

    return (
        <nav>
            <ul className="list list--accordion list--no-margin">
                {
                    steps.map( (step, index) => (
                        <FormStepNavItem
                            key={index}
                            name={step.isNew
                                ? (intl.formatMessage({
                                    description: 'form step label in nav',
                                    defaultMessage: '{name} [new]'
                                    }, {name: step.name})
                                )
                                : step.name
                            }
                            hasErrors={step.validationErrors.length > 0}
                            active={Boolean(active && step.index === steps.indexOf(active))}
                            onActivate={ () => onActivateStep(index) }
                            onReorder={onReorder.bind(null, index)}
                            onDelete={onDelete.bind(null, index)}
                        />
                    ))
                }
                <li className="list__item">
                    <button type="button" onClick={onStepAdd} className="button button--plain button--center">
                        <span className="addlink">
                            <FormattedMessage description="add step button" defaultMessage="Add step" />
                        </span>
                    </button>
                </li>
            </ul>
        </nav>
    );
};

FormStepsNav.propTypes = {
    steps: PropTypes.arrayOf(PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        name: PropTypes.string,
        slug: PropTypes.string,
        url: PropTypes.string,
        isNew: PropTypes.bool,
    })),
    active: PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        name: PropTypes.string,
        slug: PropTypes.string,
        url: PropTypes.string,
    }),
    onActivateStep: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
};


export default FormStepsNav;

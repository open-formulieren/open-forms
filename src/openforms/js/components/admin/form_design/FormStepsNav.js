import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import FAIcon from '../FAIcon';


const FormStepNavItem = ({ name, active=false, onActivate, onReorder, onDelete }) => {
    const className = classNames(
        'list__item',
        'list__item--with-actions',
        {'list__item--active': active},
    );
    return (
        <li className={className}>
            <div className="actions actions--vertical">
                <FAIcon icon="angle-up" title="Move up" extraClassname="fa-lg actions__action" onClick={ () => onReorder('up') } />
                <FAIcon icon="angle-down" title="Move down" extraClassname="fa-lg actions__action" onClick={ () => onReorder('down') } />
            </div>
            <button type="button" onClick={onActivate} className="button button--plain">
                {name}
            </button>
            <div className="actions">
                <FAIcon icon="trash" extraClassname="icon icon--danger actions__action" title="Delete" onClick={onDelete} />
            </div>
        </li>
    );
};

FormStepNavItem.propTypes = {
    name: PropTypes.string.isRequired,
    active: PropTypes.bool.isRequired,
    onActivate: PropTypes.func.isRequired,
    onReorder: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};


const FormStepsNav = ({ steps=[], active=null, onActivateStep, onReorder, onDelete, onAdd }) => {

    const confirmDelete = (index) => {
        const step = steps[index];
        if(window.confirm(`Weet je zeker dat je de stap '${step.name}' wil verwijderen?`)){
            onDelete(index);
        }
    };

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
                            name={ step.isNew ? `${step.name} [nieuw]` : step.name}
                            active={Boolean(active && step.index === steps.indexOf(active))}
                            onActivate={ () => onActivateStep(index) }
                            onReorder={onReorder.bind(null, index)}
                            onDelete={confirmDelete.bind(null, index)}
                        />
                    ))
                }
                <li className="list__item">
                    <button type="button" onClick={onStepAdd} className="button button--plain button--center">
                        <span className="addlink">Add step</span>
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

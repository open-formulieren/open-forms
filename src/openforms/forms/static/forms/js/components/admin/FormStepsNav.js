import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';


const FormStepNavItem = ({ name, active=false, onActivate }) => {
    const className = classNames(
        'list__item',
        {'list__item--active': active},
    );
    return (
        <li className={className}>
            <button type="button" onClick={onActivate} className="button button--plain">
                {name}
            </button>
        </li>
    );
};

FormStepNavItem.propTypes = {
    name: PropTypes.string.isRequired,
    active: PropTypes.bool.isRequired,
    onActivate: PropTypes.func.isRequired,
};


const FormStepsNav = ({ steps=[], active=null, onActivateStep }) => {

    return (
        <nav>
            <ul className="list list--accordion list--no-margin">
                {
                    steps.map( step => (
                        <FormStepNavItem
                            key={step.slug}
                            name={step.name}
                            active={step === active}
                            onActivate={ () => onActivateStep(step) } />
                    ))
                }
                <li className="list__item">
                    <button type="button" onClick={console.log} className="button button--plain">
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
};


export default FormStepsNav;

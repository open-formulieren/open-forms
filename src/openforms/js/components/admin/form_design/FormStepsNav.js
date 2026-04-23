import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from './Context';
import {FormStepNavMultipleItems, FormStepNavSingleItem} from './FormStepsNavItem';

const FormStepsNav = ({steps = [], active = null, onActivateStep, onReorder, onDelete, onAdd}) => {
  const intl = useIntl();
  const {
    form: {type},
  } = useContext(FormContext);

  const isSinglePage = type === 'single_step';

  const onStepAdd = event => {
    onAdd(event);
    onActivateStep(steps.length);
  };

  return (
    <nav>
      {isSinglePage && steps.length > 0 ? (
        <ul className="list list--accordion list--no-margin">
          <FormStepNavSingleItem
            // single page is already disabled if more than one steps are configured
            key={steps[0].index}
            name={
              steps[0].isNew
                ? intl.formatMessage(
                    {
                      description: 'form step label in nav',
                      defaultMessage: '{name} [new]',
                    },
                    {name: steps[0]?.name}
                  )
                : steps[0]?.name
            }
            hasErrors={steps[0].validationErrors.length > 0}
            active={Boolean(active && steps[0].index === steps.indexOf(active))}
            onActivate={() => onActivateStep(steps[0].index)}
            onDelete={onDelete.bind(null, steps[0].index)}
          />
        </ul>
      ) : (
        <ul className="list list--accordion list--no-margin">
          {steps.map((step, index) => (
            <FormStepNavMultipleItems
              key={index}
              name={
                step.isNew
                  ? intl.formatMessage(
                      {
                        description: 'form step label in nav',
                        defaultMessage: '{name} [new]',
                      },
                      {name: step.name}
                    )
                  : step.name
              }
              hasErrors={step.validationErrors.length > 0}
              active={Boolean(active && step.index === steps.indexOf(active))}
              onActivate={() => onActivateStep(index)}
              onReorder={onReorder.bind(null, index)}
              onDelete={onDelete.bind(null, index)}
            />
          ))}
          <li className="list__item">
            <button
              type="button"
              onClick={onStepAdd}
              className="button button--plain button--center"
            >
              <span className="addlink">
                <FormattedMessage description="add step button" defaultMessage="Add step" />
              </span>
            </button>
          </li>
        </ul>
      )}
    </nav>
  );
};

FormStepsNav.propTypes = {
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      configuration: PropTypes.object,
      formDefinition: PropTypes.string,
      index: PropTypes.number,
      name: PropTypes.string,
      slug: PropTypes.string,
      url: PropTypes.string,
      isNew: PropTypes.bool,
    })
  ),
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

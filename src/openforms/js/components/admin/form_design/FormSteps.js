import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage} from 'react-intl';

import Loader from 'components/admin/Loader';
import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';

import {FormStepContext} from './Context';
import FormStep from './FormStep';
import FormStepsNav from './FormStepsNav';

const FormSteps = ({
  steps = [],
  onEdit,
  onComponentMutated,
  onFieldChange,
  onDelete,
  onReorder,
  onReplace,
  onAdd,
  submitting = false,
}) => {
  const [activeStepIndex, setActiveStepIndex] = useState(steps.length ? 0 : null);
  const activeStep = steps.length ? steps[activeStepIndex] : null;

  const className = classNames('edit-panel', {'edit-panel--submitting': submitting});

  return (
    <section className={className}>
      {submitting ? (
        <div className="edit-panel__submit-layer">
          <Loader />
        </div>
      ) : null}
      <div className="edit-panel__nav">
        <FormStepsNav
          steps={steps}
          active={activeStep}
          onActivateStep={setActiveStepIndex}
          onReorder={onReorder}
          onDelete={onDelete}
          onAdd={onAdd}
        />
      </div>
      <div className="edit-panel__edit-area">
        {activeStep ? (
          <FormStepContext.Provider
            value={{componentTranslations: activeStep.componentTranslations || {}}}
          >
            <ValidationErrorsProvider errors={activeStep.validationErrors}>
              <FormStep
                data={activeStep}
                onEdit={onEdit.bind(null, activeStepIndex)}
                onComponentMutated={onComponentMutated}
                onFieldChange={onFieldChange.bind(null, activeStepIndex)}
                onReplace={onReplace.bind(null, activeStepIndex)}
              />
            </ValidationErrorsProvider>
          </FormStepContext.Provider>
        ) : (
          <FormattedMessage
            defaultMessage="Select a step to view or modify."
            description="No-active-step-selected notice"
          />
        )}
      </div>
    </section>
  );
};

FormSteps.propTypes = {
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      configuration: PropTypes.object,
      formDefinition: PropTypes.string,
      index: PropTypes.number,
      name: PropTypes.string,
      slug: PropTypes.string,
      url: PropTypes.string,
      isNew: PropTypes.bool,
      validationErrors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
    })
  ),
  onEdit: PropTypes.func.isRequired,
  onComponentMutated: PropTypes.func.isRequired,
  onFieldChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onReorder: PropTypes.func.isRequired,
  onReplace: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
  submitting: PropTypes.bool,
};

export default FormSteps;

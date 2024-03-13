import PropTypes from 'prop-types';
import React from 'react';
import usePrevious from 'react-use/esm/usePrevious';

import FormStepDefinition from './FormStepDefinition';
import NewStepFormDefinitionPicker from './NewStepFormDefinitionPicker';
import TYPES from './types';

const FormStep = ({data, onEdit, onComponentMutated, onFieldChange, onReplace}) => {
  const {
    _generatedId,
    index,
    configuration,
    formDefinition,
    name,
    internalName,
    slug,
    loginRequired,
    translations,
    isApplicable,
    isReusable,
    isNew,
    validationErrors = [],
  } = data;
  const previousFormDefinition = usePrevious(formDefinition);
  let forceBuilderUpdate = false;
  if (previousFormDefinition && previousFormDefinition != formDefinition) {
    forceBuilderUpdate = true;
  }
  // FIXME: find a more robust way than just looking at the step name
  const prevName = usePrevious(name);
  if (!forceBuilderUpdate && prevName && prevName != name) {
    forceBuilderUpdate = true;
  }

  if (isNew) {
    return <NewStepFormDefinitionPicker onReplace={onReplace} />;
  }

  return (
    <FormStepDefinition
      internalName={internalName}
      index={index}
      slug={slug}
      url={formDefinition}
      generatedId={_generatedId}
      translations={translations}
      configuration={configuration}
      isApplicable={isApplicable}
      loginRequired={loginRequired}
      isReusable={isReusable}
      onFieldChange={onFieldChange}
      onChange={onEdit}
      onComponentMutated={onComponentMutated}
      forceUpdate={forceBuilderUpdate}
      errors={validationErrors}
    />
  );
};

FormStep.propTypes = {
  data: TYPES.FormStep.isRequired,
  onEdit: PropTypes.func.isRequired,
  onComponentMutated: PropTypes.func.isRequired,
  onFieldChange: PropTypes.func.isRequired,
  onReplace: PropTypes.func.isRequired,
};

export default FormStep;

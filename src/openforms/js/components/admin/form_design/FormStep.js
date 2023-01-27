import PropTypes from 'prop-types';
import React from 'react';
import usePrevious from 'react-use/esm/usePrevious';

import FormStepDefinition from './FormStepDefinition';
import NewStepFormDefinitionPicker from './NewStepFormDefinitionPicker';

const FormStep = ({data, onEdit, onComponentMutated, onFieldChange, onReplace}) => {
  const {
    _generatedId,
    configuration,
    formDefinition,
    name,
    internalName,
    slug,
    loginRequired,
    translations,
    isReusable,
    isNew,
    validationErrors = [],
    componentTranslations = {},
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
      slug={slug}
      url={formDefinition}
      generatedId={_generatedId}
      translations={translations}
      componentTranslations={componentTranslations}
      configuration={configuration}
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
  data: PropTypes.shape({
    configuration: PropTypes.object,
    formDefinition: PropTypes.string,
    index: PropTypes.number,
    name: PropTypes.string,
    internalName: PropTypes.string,
    slug: PropTypes.string,
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
  }).isRequired,
  onEdit: PropTypes.func.isRequired,
  onComponentMutated: PropTypes.func.isRequired,
  onFieldChange: PropTypes.func.isRequired,
  onReplace: PropTypes.func.isRequired,
};

export default FormStep;

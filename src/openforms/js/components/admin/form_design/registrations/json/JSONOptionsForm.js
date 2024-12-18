import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Fieldset from 'components/admin/forms/Fieldset';
import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

// TODO-4098: maybe create separate file (JSONOptionsFormFields) for all the fields?
//  Though, no need to use multiple FieldSets, so adding the fields to the form is pretty
//  straightforward.
import FormVariablesSelect from './fields/FormVariablesSelect';
import RelativeAPIEndpoint from './fields/RelativeAPIEndpoint';
// import Service from './fields/Service';


const JSONOptionsForm = ({name, label, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  // Get form variables
  const formContext = useContext(FormContext)
  const formVariables = formContext.formVariables ?? [];
  const staticVariables = formContext.staticVariables ?? [];
  const allFormVariables = staticVariables.concat(formVariables);

  const formVariableOptions = [];
  for (const formVariable of allFormVariables) {
    formVariableOptions.push({value: formVariable.key, label: formVariable.name})
  }

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={relevantErrors.length}
      modalTitle={
        <FormattedMessage
          description="JSON registration options modal title"
          defaultMessage="Plugin configuration: JSON"
        />
      }
      initialFormData={{...formData}}
      onSubmit={values => onChange({formData: values})}
      modalSize="small"
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          {/*<Service />*/}
          <RelativeAPIEndpoint />
          <FormVariablesSelect options={formVariableOptions}/>
        </Fieldset>
      </ValidationErrorsProvider>
    </ModalOptionsConfiguration>
  );
};

JSONOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  formData: PropTypes.shape({
    relativeApiEndpoint: PropTypes.string,
    // TODO-4098: might need to rename this to selectedFormVariables to avoid confusion or even
    //  naming conflicts
    formVariables: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
};

export default JSONOptionsForm;

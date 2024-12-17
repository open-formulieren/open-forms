import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

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

  const formVariableOptions = [
    {value: "1", label: "One"},
    {value: "2", label: "Two"},
    {value: "3", label: "Three"},
  ]

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
      initialFormData={{relativeApiEndpoint: '', ...formData}}
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
    formVariables: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
};

export default JSONOptionsForm;

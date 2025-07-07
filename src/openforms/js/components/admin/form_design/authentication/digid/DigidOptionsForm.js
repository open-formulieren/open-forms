import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';

import DigidOptionsFormFields from './DigidOptionsFormFields';

const DigidOptionsForm = ({name, label, plugin, authBackend, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="DigiD authentication options modal title"
          defaultMessage="Plugin configuration: DigiD"
        />
      }
      initialFormData={{...authBackend.options}}
      onSubmit={values => onChange({formData: values})}
    >
      <DigidOptionsFormFields name={name} plugin={plugin} />
    </ModalOptionsConfiguration>
  );
};

DigidOptionsForm.propType = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    options: PropTypes.shape({
      loa: PropTypes.string,
    }),
  }).isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    providesAuth: PropTypes.oneOf([['bsn']]).isRequired,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        loa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
      }),
    }).isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default DigidOptionsForm;

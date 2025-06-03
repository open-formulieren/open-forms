import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';

import YiviOptionsFormFields from './YiviOptionsFormFields';

const YiviOptionsForm = ({name, label, plugin, authBackend, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="Yivi authentication options modal title"
          defaultMessage="Plugin configuration: Yivi"
        />
      }
      initialFormData={{...authBackend.options}}
      onSubmit={values => onChange({formData: values})}
    >
      <YiviOptionsFormFields name={name} plugin={plugin} />
    </ModalOptionsConfiguration>
  );
};

YiviOptionsForm.propType = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    // Options configuration shape is specific to plugin
    options: PropTypes.shape({
      authenticationOptions: PropTypes.arrayOf(PropTypes.string),
      additionalAttributesGroups: PropTypes.arrayOf(PropTypes.string),
      bsnLoa: PropTypes.string,
      kvkLoa: PropTypes.string,
    }),
  }).isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.arrayOf(PropTypes.string),
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        authenticationOptions: PropTypes.exact({
          type: PropTypes.oneOf(['array']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          items: PropTypes.exact({
            type: PropTypes.oneOf(['string']).isRequired,
            enum: PropTypes.arrayOf(PropTypes.string).isRequired,
            enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
          }),
        }).isRequired,
        additionalAttributesGroups: PropTypes.exact({
          type: PropTypes.oneOf(['array']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          items: PropTypes.exact({
            type: PropTypes.oneOf(['string']).isRequired,
            enum: PropTypes.arrayOf(PropTypes.string).isRequired,
            enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
          }),
        }).isRequired,
        bsnLoa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }),
        kvkLoa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }),
      }),
    }),
  }),
  onChange: PropTypes.func.isRequired,
};

export default YiviOptionsForm;

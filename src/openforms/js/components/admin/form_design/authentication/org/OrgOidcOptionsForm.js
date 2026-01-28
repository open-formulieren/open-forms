import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';

import OrgOidcOptionsFormFields from './OrgOidcOptionsFormFields';

const OrgOidcOptionsForm = ({name, label, plugin, authBackend, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="OpenID Connect authentication options modal title"
          defaultMessage="Plugin configuration: Organization via OpenID Connect"
        />
      }
      initialFormData={{...authBackend.options}}
      onSubmit={values => onChange({formData: values})}
    >
      <OrgOidcOptionsFormFields name={name} />
    </ModalOptionsConfiguration>
  );
};

OrgOidcOptionsForm.propType = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    options: {},
  }).isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    providesAuth: PropTypes.oneOf([['employee_id']]).isRequired,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        visible: PropTypes.exact({
          type: PropTypes.oneOf(['boolean']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
        }).isRequired,
      }),
    }).isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default OrgOidcOptionsForm;

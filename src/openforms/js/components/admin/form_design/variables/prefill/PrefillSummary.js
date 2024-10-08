import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {normalizeErrors} from 'components/admin/forms/Field';
import {EditIcon, ErrorIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {IDENTIFIER_ROLE_CHOICES} from '../constants';
import PrefillConfigurationForm from './PrefillConfigurationForm';

const PrefillSummary = ({
  plugin = '',
  attribute = '',
  identifierRole = 'main',
  options = undefined,
  onChange = undefined,
  errors = {},
}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const identifierRoleMsg = IDENTIFIER_ROLE_CHOICES[identifierRole] || IDENTIFIER_ROLE_CHOICES.main;

  const [hasPluginErrors, pluginErrors] = normalizeErrors(errors.prefillPlugin, intl);
  const [hasAttributeErrors, attributeErrors] = normalizeErrors(errors.prefillAttribute, intl);
  const [hasIdentifierRoleErrors, identifierRoleErrors] = normalizeErrors(
    errors.prefillIdentifierRole,
    intl
  );

  const hasErrors = hasPluginErrors || hasAttributeErrors || hasIdentifierRoleErrors;

  const icons = (
    <div style={{display: 'flex', gap: '6px', alignItems: 'center'}}>
      {hasErrors && (
        <span className="icon icon--danger icon--compact icon--no-pointer">
          <ErrorIcon
            text={intl.formatMessage({
              description: 'Prefill configuration errors icon text',
              defaultMessage: 'There are errors in the prefill configuration.',
            })}
          />
        </span>
      )}
      {/* Modal control */}
      {onChange && (
        <EditIcon
          label={intl.formatMessage({
            defaultMessage: 'Edit prefill configuration',
            description: "'Edit variable prefill' icon label",
          })}
          onClick={() => setModalOpen(!modalOpen)}
        />
      )}
    </div>
  );

  return (
    <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
      {plugin === '' && attribute === '' ? (
        '-'
      ) : (
        <FormattedMessage
          tagName="span"
          description="Prefill configuration summary"
          defaultMessage="<code>{attr}</code> from <code>{plugin}</code> (of the {role})"
          values={{
            plugin,
            attr: attribute,
            role: intl.formatMessage(identifierRoleMsg),
            code: chunks => <code>{chunks}</code>,
          }}
        />
      )}

      {icons}
      {onChange && (
        <FormModal
          title={
            <FormattedMessage
              description="Variable prefill configuration modal title"
              defaultMessage="Prefill configuration"
            />
          }
          isOpen={modalOpen}
          closeModal={() => setModalOpen(false)}
        >
          <ErrorBoundary>
            <PrefillConfigurationForm
              plugin={plugin}
              attribute={attribute}
              identifierRole={identifierRole}
              options={options}
              onSubmit={values => {
                onChange(values);
                setModalOpen(false);
              }}
              errors={{
                plugin: pluginErrors,
                attribute: attributeErrors,
                identifierRole: identifierRoleErrors,
              }}
            />
          </ErrorBoundary>
        </FormModal>
      )}
    </div>
  );
};

const AnyError = PropTypes.oneOfType([
  PropTypes.string,
  PropTypes.arrayOf(PropTypes.string),
  PropTypes.object, // could be an intl message definition
]);

PrefillSummary.propTypes = {
  plugin: PropTypes.string,
  attribute: PropTypes.string,
  identifierRole: PropTypes.string,
  options: PropTypes.object,
  onChange: PropTypes.func, // if defined, we can edit it in a modal
  errors: PropTypes.objectOf(AnyError),
};

export default PrefillSummary;

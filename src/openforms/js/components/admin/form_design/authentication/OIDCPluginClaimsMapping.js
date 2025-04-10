import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import {TextInput} from 'components/admin/forms/Inputs';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {DeleteIcon, FAIcon} from 'components/admin/icons';

const VariableMappingRow = ({prefix, claimMapping, onChange, onRemove}) => {
  const intl = useIntl();

  return (
    <tr>
      <td>
        <Field name={`${prefix}.claimName`}>
          <TextInput
            name={`${prefix}.claimName`}
            value={claimMapping.claimName}
            onChange={onChange}
            aria-label={intl.formatMessage({
              defaultMessage: 'Claim name',
              description: 'Claim name label',
            })}
          />
        </Field>
      </td>

      <td className="mapping-table__direction-icon">
        <FAIcon icon="arrow-right-long" aria-hidden="true" />
      </td>

      <td>
        <Field name={`${prefix}.formVariable`}>
          <VariableSelection
            name={`${prefix}.formVariable`}
            value={claimMapping.formVariable}
            onChange={onChange}
            aria-label={intl.formatMessage({
              description: 'Accessible label for (form) variable dropdown',
              defaultMessage: 'Form variable',
            })}
          />
        </Field>
      </td>

      <td>
        <DeleteIcon
          onConfirm={onRemove}
          message={intl.formatMessage({
            description: 'Confirmation message to remove a mapping',
            defaultMessage: 'Are you sure that you want to remove this mapping?',
          })}
        />
      </td>
    </tr>
  );
};

VariableMappingRow.propTypes = {
  prefix: PropTypes.string.isRequired,
  claimMapping: PropTypes.shape({
    claimName: PropTypes.string,
    formVariable: PropTypes.string,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
};

/**
 * Map extra auth claim names to form variables.
 *
 * Inspired on the `VariableMapping` component - we can't re-use that one because the
 * claim names can be (and probably are) different for each form.
 *
 * @todo consider making the `VariableMapping`` component more flexible?
 *
 */
const OIDCPluginClaimsMapping = ({prefix, availableAuthPlugins, pluginClaims, onChange}) => {
  const plugin = availableAuthPlugins.find(plugin => plugin.id === pluginClaims.pluginId);
  if (!plugin) {
    return null;
  }

  return (
    <>
      <FormattedMessage
        tagName="span"
        description="Plugin name"
        defaultMessage="Plugin: {plugin}"
        values={{
          plugin: plugin.label,
        }}
      />
      <div className={'mapping-table'} style={{marginBlockStart: '10px'}}>
        <table>
          <thead>
            <tr>
              <th>
                <FormattedMessage defaultMessage="Claim name" description="Claim name label" />
              </th>
              <th />
              <th>
                <FormattedMessage
                  defaultMessage="Open Forms variable"
                  description="Open Forms variable label"
                />
              </th>
              <th />
            </tr>
          </thead>

          <tbody>
            {pluginClaims.claimMapping.map((claimMapping, index) => (
              <VariableMappingRow
                key={index}
                prefix={`${prefix}.claimMapping.${index}`}
                claimMapping={claimMapping}
                onChange={onChange}
                onRemove={() =>
                  onChange({
                    target: {
                      name: prefix,
                      value: {
                        ...pluginClaims,
                        claimMapping: pluginClaims.claimMapping.filter(
                          _,
                          mappingIndex => mappingIndex !== index
                        ),
                      },
                    },
                  })
                }
              />
            ))}
          </tbody>
        </table>

        <ButtonContainer
          onClick={() =>
            onChange({
              target: {
                name: prefix,
                value: {
                  ...pluginClaims,
                  claimMapping: [...pluginClaims.claimMapping, {claimName: '', formVariable: ''}],
                },
              },
            })
          }
        >
          <FormattedMessage description="Add claim button" defaultMessage="Add claim" />
        </ButtonContainer>
      </div>
    </>
  );
};

OIDCPluginClaimsMapping.propTypes = {
  prefix: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.string,
    })
  ).isRequired,
  pluginClaims: PropTypes.shape({
    pluginId: PropTypes.string.isRequired,
    claimMapping: PropTypes.arrayOf(
      PropTypes.shape({
        claimName: PropTypes.string,
        formVariable: PropTypes.string,
      })
    ).isRequired,
  }).isRequired,
};

export default OIDCPluginClaimsMapping;

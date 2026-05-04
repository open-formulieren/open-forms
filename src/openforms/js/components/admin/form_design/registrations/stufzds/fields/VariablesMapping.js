import {FieldArray, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext, useEffect} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {DeleteIcon, FAIcon} from 'components/admin/icons';

import {PLUGIN_ID} from '../constants';

const VariableMappingRow = ({prefix, onRemove}) => {
  const {formVariables = []} = useContext(FormContext);
  const intl = useIntl();
  const {getFieldProps, setFieldValue} = useFormikContext();

  const stufNameProps = getFieldProps(`${prefix}.stufName`);
  const serializeListToCsvProps = getFieldProps({
    name: `${prefix}.serializeListToCsv`,
    type: 'checkbox',
  });

  const selectedFormVariable = getFieldProps(`${prefix}.formVariable`).value;
  const formVariable = formVariables.find(fv => fv.key === selectedFormVariable);
  const isArrayFormVariable = formVariable && formVariable.dataType === 'array';

  useEffect(() => {
    if (!isArrayFormVariable && serializeListToCsvProps.checked) {
      setFieldValue(`${prefix}.serializeListToCsv`, false);
    }
  }, [setFieldValue, prefix, isArrayFormVariable, serializeListToCsvProps.checked]);

  return (
    <tr>
      <td>
        <Field name={`${prefix}.formVariable`}>
          <VariableSelection
            includeStaticVariables
            {...getFieldProps(`${prefix}.formVariable`)}
            aria-label={intl.formatMessage({
              description: 'Accessible label for (form) variable dropdown',
              defaultMessage: 'Form variable',
            })}
          />
        </Field>
      </td>

      <td className="mapping-table__direction-icon">
        <FAIcon icon="arrow-right-long" aria-hidden="true" />
      </td>

      <td>
        <Field name={`${prefix}.stufName`}>
          <TextInput
            {...stufNameProps}
            aria-label={intl.formatMessage({
              defaultMessage: 'StUF-ZDS name',
              description: 'StUF-ZDS extraElement name label',
            })}
          />
        </Field>
      </td>

      <td>
        {isArrayFormVariable ? (
          <Checkbox
            {...serializeListToCsvProps}
            aria-label={intl.formatMessage({
              description: 'StUF-ZDS extraElement serializeListToCsv label',
              defaultMessage: 'Comma-separate list values',
            })}
            disabled={false}
          />
        ) : (
          '-'
        )}
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
  onRemove: PropTypes.func.isRequired,
};

/**
 * Map (registration) form variables to extraElementen names.
 *
 * Inspired on the `VariableMapping` component - we can't re-use that one because we
 * don't (yet) receive dropdowns/form variable context from the backend to display
 * options in a dropdown for the StUF extraElementen targets.
 */
const VariablesMapping = ({name}) => {
  const formContext = useContext(FormContext);

  const pluginVariables =
    formContext.registrationPluginsVariables.find(entry => entry.pluginIdentifier === PLUGIN_ID)
      ?.pluginVariables ?? [];

  const formVariables = pluginVariables.concat(formContext.formVariables);

  const {getFieldProps} = useFormikContext();
  const {value: mappings = []} = getFieldProps(name);

  return (
    // use a new Form Context and let the registration variables shadow the normal form
    // variables, so that the form variable dropdown can be re-used.
    <FormContext.Provider value={{...formContext, formVariables}}>
      <FieldArray
        name={name}
        render={arrayHelpers => (
          <div className={'mapping-table'} style={{marginBlockStart: '10px'}}>
            <table>
              <thead>
                <tr>
                  <th>
                    <FormattedMessage
                      defaultMessage="Open Forms variable"
                      description="Open Forms variable label"
                    />
                  </th>
                  <th />
                  <th>
                    <FormattedMessage
                      defaultMessage="StUF-ZDS name"
                      description="StUF-ZDS extraElement name label"
                    />
                  </th>
                  <th>
                    <FormattedMessage
                      description="StUF-ZDS extraElement serializeListToCsv label"
                      defaultMessage="Comma-separate list values"
                    />
                  </th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {mappings.map((_, index) => (
                  <VariableMappingRow
                    key={index}
                    prefix={`${name}.${index}`}
                    onRemove={() => arrayHelpers.remove(index)}
                  />
                ))}
              </tbody>
            </table>

            <ButtonContainer
              onClick={() => {
                arrayHelpers.insert(mappings.length, {
                  formVariable: '',
                  stufName: '',
                  serializeListToCsv: false,
                });
              }}
            >
              <FormattedMessage description="Add variable button" defaultMessage="Add variable" />
            </ButtonContainer>
          </div>
        )}
      />
    </FormContext.Provider>
  );
};

VariablesMapping.propTypes = {
  name: PropTypes.string.isRequired,
};

export default VariablesMapping;

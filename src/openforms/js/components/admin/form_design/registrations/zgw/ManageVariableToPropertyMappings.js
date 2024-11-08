import classNames from 'classnames';
import {FieldArray, useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {getComponentDatatype} from 'components/admin/form_design/variables/utils';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import ComponentSelection from 'components/admin/forms/ComponentSelection';
import Field from 'components/admin/forms/Field';
import {TextInput} from 'components/admin/forms/Inputs';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';
import {DeleteIcon} from 'components/admin/icons';
import {ChangelistTableWrapper, HeadColumn, TableRow} from 'components/admin/tables';

const HeadColumns = () => {
  const intl = useIntl();

  const componentText = intl.formatMessage({
    description: 'Column title for variable to map to property',
    defaultMessage: 'Variable',
  });
  const componentHelp = intl.formatMessage({
    description: 'Column help text for variable to map to property',
    defaultMessage: 'The value of the selected field will be the process variable value.',
  });

  const eigenschapText = intl.formatMessage({
    description: 'Column title for case property that a variable is mapped to',
    defaultMessage: 'Property',
  });

  const eigenschapHelp = intl.formatMessage({
    description: 'Column help text for case property that a variable is mapped to',
    defaultMessage: 'Specify a ZGW property name.',
  });

  return (
    <>
      <HeadColumn content="" />
      <HeadColumn content={componentText} title={componentHelp} />
      <HeadColumn content={eigenschapText} title={eigenschapHelp} />
    </>
  );
};

const VariableProperty = ({index, componentKey, componentFilterFunc, onDelete}) => {
  const intl = useIntl();
  const errors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(`propertyMappings.${index}`, errors);

  const variableName = `propertyMappings.${index}.componentKey`;
  const [variableProps] = useField(variableName);
  const variableErrors = relevantErrors.filter(([key]) => key === 'componentKey');

  const eigenschapName = `propertyMappings.${index}.eigenschap`;
  const [eigenschapProps] = useField(eigenschapName);
  const eigenschapErrors = relevantErrors.filter(([key]) => key === 'eigenschap');

  const confirmDeleteMessage = intl.formatMessage({
    description: 'Delete confirmation message for variable mapped to case property',
    defaultMessage: 'Are you sure you want to remove this mapping?',
  });

  return (
    <TableRow index={index} className={classNames({'has-errors': relevantErrors.length > 0})}>
      <div className="actions actions--horizontal actions--roomy">
        <DeleteIcon onConfirm={onDelete} message={confirmDeleteMessage} />
      </div>

      <Field name={variableName} errors={variableErrors} noManageChildProps>
        <ComponentSelection filter={componentFilterFunc} {...variableProps} />
      </Field>

      <Field name={eigenschapName} errors={eigenschapErrors} noManageChildProps>
        {/* TODO - lookup available properties from the selected zaaktype */}
        <TextInput placeholder={componentKey} {...eigenschapProps} />
      </Field>
    </TableRow>
  );
};

VariableProperty.propTypes = {
  index: PropTypes.number.isRequired,
  componentKey: PropTypes.string,
  componentFilterFunc: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

const getSimpleComponentsLength = allComponents => {
  const filteredComponents = Object.keys(allComponents).filter(comp => {
    const componentDataType = getComponentDatatype(allComponents[comp]);
    return !['array', 'object'].includes(componentDataType) && comp !== 'columns';
  });

  return filteredComponents.length;
};

/**
 * @todo - check how validation errors are displayed now
 */
const ManageVariableToPropertyMappings = () => {
  const {
    values: {propertyMappings = []},
  } = useFormikContext();
  const {components: allComponents} = useContext(FormContext);

  const usedComponents = propertyMappings
    .filter(mapping => mapping.componentKey !== '')
    .map(mapping => mapping.componentKey);

  const filterFunc = (componentKey, component) => {
    const isSimpleType =
      !['array', 'object'].includes(getComponentDatatype(component)) && component.key !== 'columns';
    const componentNotUsed =
      componentKey === component.key || !usedComponents.includes(component.key);

    return isSimpleType && componentNotUsed;
  };

  const numSimpleComponents = getSimpleComponentsLength(allComponents);
  return (
    <FieldArray name="propertyMappings">
      {arrayHelpers => (
        <>
          <ChangelistTableWrapper headColumns={<HeadColumns />}>
            {propertyMappings.map(({componentKey}, index) => (
              <VariableProperty
                key={index}
                index={index}
                componentKey={componentKey}
                componentFilterFunc={filterFunc.bind(null, componentKey)}
                onDelete={() => arrayHelpers.remove(index)}
              />
            ))}
          </ChangelistTableWrapper>

          {usedComponents.length < numSimpleComponents ? (
            <ButtonContainer
              onClick={() =>
                arrayHelpers.insert(propertyMappings.length, {
                  componentKey: '',
                  eigenschap: '',
                })
              }
            >
              <FormattedMessage
                description="Add zaakeigenschap (mapping) button"
                defaultMessage="Add variable"
              />
            </ButtonContainer>
          ) : (
            <FormattedMessage
              description="Warning that all simple variables are mapped"
              defaultMessage="All simple variables are mapped to a case property."
            />
          )}
        </>
      )}
    </FieldArray>
  );
};

ManageVariableToPropertyMappings.propTypes = {};

export default ManageVariableToPropertyMappings;

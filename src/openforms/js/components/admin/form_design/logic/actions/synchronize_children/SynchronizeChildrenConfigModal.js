import classNames from 'classnames';
import {FieldArray, Form, Formik, getIn, useField, useFormikContext} from 'formik';
import {useContext} from 'react';
import {FormattedMessage, intl, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {getComponentDatatype} from 'components/admin/form_design/variables/utils';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import ComponentSelection from 'components/admin/forms/ComponentSelection';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';
import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';
import {DeleteIcon} from 'components/admin/icons';
import {ChangelistTableWrapper, HeadColumn, TableRow} from 'components/admin/tables';

const ALLOWED_PROPERTIES = [
  {id: 'id_bsn', name: 'BSN'},
  {id: 'id_firstNames', name: 'First names'},
];

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

  const allowedPropertyText = intl.formatMessage({
    description: 'Column title for the allowed property that a variable is mapped to',
    defaultMessage: 'Property',
  });

  const allowedPropertyHelp = intl.formatMessage({
    description: 'Column help text for the allowed property that a variable is mapped to',
    defaultMessage: 'Select a property name.',
  });

  return (
    <>
      <HeadColumn content="" />
      <HeadColumn content={componentText} title={componentHelp} />
      <HeadColumn content={allowedPropertyText} title={allowedPropertyHelp} />
    </>
  );
};

const ChildrenMapping = ({
  keyMapping,
  index,
  componentFilterFunc,
  allowedPropertyOptions,
  onDelete,
}) => {
  const intl = useIntl();
  const errors = useContext(ValidationErrorContext);
  const {values, setFieldValue} = useFormikContext();
  const relevantErrors = filterErrors(`childrenMappings.${index}`, errors);
  const variableName = `childrenMappings.${index}.formVariable`;
  const [variableProps] = useField(variableName);
  const variableErrors = relevantErrors.filter(([key]) => key === 'formVariable');

  const confirmDeleteMessage = intl.formatMessage({
    description: 'Delete confirmation message for property mapped to variable',
    defaultMessage: 'Are you sure you want to remove this mapping?',
  });

  const allowedPropertyName = `childrenMappings.${index}.allowedProperty`;

  return (
    <TableRow index={index} className={classNames({'has-errors': relevantErrors.length > 0})}>
      <div className="actions actions--horizontal actions--roomy">
        <DeleteIcon onConfirm={onDelete} message={confirmDeleteMessage} />
      </div>

      <Field name={variableName} errors={variableErrors} noManageChildProps>
        <ComponentSelection filter={componentFilterFunc} {...variableProps} />
      </Field>

      <Field name={allowedPropertyName}>
        <Select
          key={keyMapping}
          name={allowedPropertyName}
          choices={allowedPropertyOptions.map(property => [property.id, property.name])}
          onChange={e => {
            const selectedId = e.target.value;
            setFieldValue(allowedPropertyName, selectedId);
          }}
          value={getIn(values, allowedPropertyName) || ''}
          allowBlank
        />
      </Field>
    </TableRow>
  );
};

const ManageChildrenMappings = () => {
  const {
    values: {childrenMappings = []},
  } = useFormikContext();

  const usedProperties = childrenMappings.map(mapping => mapping.allowedProperty).filter(Boolean);
  const allPropertiesMapped = usedProperties.length >= ALLOWED_PROPERTIES.length;

  const simpleComponentFilterFunc = component => {
    return (
      !['array', 'object'].includes(getComponentDatatype(component)) && component.key !== 'columns'
    );
  };

  const availablePropertiesForRow = currentAllowedProperty =>
    ALLOWED_PROPERTIES.filter(
      property => property.id === currentAllowedProperty || !usedProperties.includes(property.id)
    );

  return (
    <FieldArray name="childrenMappings">
      {arrayHelpers => (
        <>
          <ChangelistTableWrapper headColumns={<HeadColumns />}>
            {childrenMappings.map(({allowedProperty}, index) => {
              const allowedPropertyOptions = availablePropertiesForRow(allowedProperty);

              return (
                <ChildrenMapping
                  key={index}
                  index={index}
                  componentFilterFunc={simpleComponentFilterFunc}
                  allowedPropertyOptions={allowedPropertyOptions}
                  onDelete={() => arrayHelpers.remove(index)}
                />
              );
            })}
          </ChangelistTableWrapper>

          {!allPropertiesMapped ? (
            <ButtonContainer
              onClick={() =>
                arrayHelpers.insert(childrenMappings.length, {
                  formVariable: '',
                  allowedProperty: '',
                })
              }
            >
              <FormattedMessage
                description="Add children (mapping) button"
                defaultMessage="Add variable"
              />
            </ButtonContainer>
          ) : (
            <FormattedMessage
              description="Warning that all possible properties are mapped"
              defaultMessage="All possible properties are mapped to a simple component."
            />
          )}
        </>
      )}
    </FieldArray>
  );
};

const SynchronizeChildrenActionConfig = ({initialValues, onSave, errors = {}}) => {
  const {formVariables} = useContext(FormContext);

  const relevantvariables = formVariables.filter(
    variable => variable.dataType === 'array' && variable.source === 'component'
  );

  return (
    <ValidationErrorsProvider errors={Object.entries(errors)}>
      <div className="synchronize-children-action-config">
        <Formik
          initialValues={{
            ...initialValues,
          }}
          onSubmit={values => onSave(values)}
        >
          {({values, setFieldValue}) => (
            <Form>
              <Fieldset>
                <FormRow>
                  <Field
                    name="sourceVariable"
                    label={
                      <FormattedMessage
                        defaultMessage="From variable"
                        description="Synchronize children modal select from variable field label"
                      />
                    }
                  >
                    <Select
                      key="sourceVariableKey"
                      name="sourceVariable"
                      choices={relevantvariables.map(variable => [variable.id, variable.key])}
                      value={values.sourceVariable}
                      onChange={e => setFieldValue('sourceVariable', e.target.value)}
                      allowBlank
                    />
                  </Field>
                </FormRow>
                <FormRow>
                  <Field
                    name="destinationVariable"
                    label={
                      <FormattedMessage
                        defaultMessage="To variable"
                        description="Synchronize children modal select to variable field label"
                      />
                    }
                  >
                    <Select
                      key="destinationVariableKey"
                      name="destinationVariable"
                      choices={relevantvariables.map(variable => [variable.id, variable.key])}
                      value={values.destinationVariable}
                      onChange={e => setFieldValue('destinationVariable', e.target.value)}
                      allowBlank
                    />
                  </Field>
                </FormRow>
                <ManageChildrenMappings />
              </Fieldset>

              <div className="submit-row">
                <input type="submit" name="_save" value="Save" />
              </div>
            </Form>
          )}
        </Formik>
      </div>
    </ValidationErrorsProvider>
  );
};

export {SynchronizeChildrenActionConfig};

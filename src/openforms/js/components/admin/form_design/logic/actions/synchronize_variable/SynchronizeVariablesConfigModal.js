import {Form, Formik, useFormikContext} from 'formik';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {getComponentDatatype} from 'components/admin/form_design/variables/utils';
import {makeNewVariableFromComponent} from 'components/admin/form_design/variables/utils';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {ValidationErrorsProvider} from 'components/admin/forms/ValidationErrors';
import VariableMapping from 'components/admin/forms/VariableMapping';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {FAIcon} from 'components/admin/icons';
import ErrorMessage from 'components/errors/ErrorMessage';

import {CHILDREN_PROPERTY_LABELS} from './constants';

const IdentifierVariable = () => {
  const {components, ...formContext} = useContext(FormContext);

  const {
    values: {destinationVariable, identifierVariable, dataMappings},
    getFieldProps,
    setFieldValue,
  } = useFormikContext();

  // Filter the components according to their type (we only want the BSN) and only the
  // nested ones of the destination variable. We create an array of fake variables for
  // them in order to make them available via the formContext in the dropdown.
  const relevantComponents = Object.entries(components)
    .filter(([objKey, _]) => objKey.startsWith(destinationVariable))
    .map(([_, componentConfig]) => componentConfig);

  const bsnRelevantComponents = relevantComponents.filter(compConfig => compConfig.type === 'bsn');
  const bsnRelevantComponentsKeys = bsnRelevantComponents.map(component => component.key);

  const identifierInMappings = dataMappings.some(mapping =>
    bsnRelevantComponentsKeys.includes(mapping.componentKey)
  );

  const bsnFakeVariables = bsnRelevantComponents.map(initialCompConfig =>
    makeNewVariableFromComponent(initialCompConfig, undefined)
  );

  const onIdentifierVariableChange = e => {
    const {name, value} = e.target;
    let updated;
    if (identifierInMappings) {
      updated = dataMappings;
    } else {
      updated = [
        ...dataMappings,
        {
          componentKey: bsnRelevantComponents[0].key,
          property: 'bsn',
          value,
        },
      ];
    }

    setFieldValue(name, value);
    setFieldValue('dataMappings', updated);
  };

  return (
    // use a new Form Context and let only the nested editgrid bsn components be available
    // in the dropdown
    <FormContext.Provider value={{...formContext, formVariables: bsnFakeVariables}}>
      <FormRow>
        <Field
          name="identifierVariable"
          label={
            <FormattedMessage
              description="Synchronize variables modal select identifierVariable field label"
              defaultMessage="Identifier variable (BSN)"
            />
          }
          required
        >
          <VariableSelection
            {...getFieldProps('identifierVariable')}
            name="identifierVariable"
            value={identifierVariable}
            onChange={onIdentifierVariableChange}
          />
        </Field>
      </FormRow>
    </FormContext.Provider>
  );
};

const ManageDataMappings = ({errors}) => {
  const intl = useIntl();

  const {
    values: {destinationVariable},
  } = useFormikContext();
  const {components, ...formContext} = useContext(FormContext);

  const relevantErrors = Object.entries(errors).filter(
    error => error[0] === 'dataMappings' && typeof error[1] === 'string'
  );

  const detectMappingProblems = (intl, {componentKey, property}) => {
    const problems = [];
    if ((!componentKey && property) || (componentKey && !property)) {
      problems.push(
        intl.formatMessage({
          description: 'Variables mappings: detected invalid mapping',
          defaultMessage: 'No component or property specified (anymore).',
        })
      );
    }
    return problems;
  };

  const propertyHeading = intl.formatMessage({
    description: 'Column title for the property that a component is mapped to',
    defaultMessage: 'Property',
  });

  // Filter the components according to their type (we only want the simple ones) and
  // only the nested ones of the destination variable.
  // We create an array of fake variables for them in order to make them available via
  // the formContext in the dropdown.
  const relevantComponents = Object.entries(components).filter(([objKey, _]) =>
    objKey.startsWith(destinationVariable)
  );
  const simpleRelevantComponents = relevantComponents.filter(
    ([, compConfig]) =>
      !['array', 'object'].includes(getComponentDatatype(compConfig)) &&
      compConfig.type !== 'columns'
  );
  const editGridFakeVariables = simpleRelevantComponents.map(([_, initialCompConfig]) =>
    makeNewVariableFromComponent(initialCompConfig, undefined)
  );

  return (
    // use a new Form Context and let only the nested editgrid components be available in
    // the dropdown
    <FormContext.Provider value={{...formContext, formVariables: editGridFakeVariables}}>
      <h3 className="react-modal__section-title">
        <FormattedMessage defaultMessage="Data mappings" description="Data mappings title" />
      </h3>

      {relevantErrors.map(([field, message], index) => (
        <ErrorMessage key={`${field}-${index}`}>{message}</ErrorMessage>
      ))}

      <VariableMapping
        loading={false}
        name="dataMappings"
        directionIcon={<FAIcon icon="arrow-left-long" aria-hidden="true" />}
        variableName="componentKey"
        propertyChoices={Object.entries(CHILDREN_PROPERTY_LABELS)}
        translatePropertyChoices
        propertyName="property"
        propertyHeading={propertyHeading}
        propertySelectLabel={propertyHeading}
        rowCheck={detectMappingProblems}
      />
    </FormContext.Provider>
  );
};

const SynchronizeVariablesActionConfig = ({initialValues, onSave, errors = {}}) => {
  const {components} = useContext(FormContext);

  function extractNonFieldErrors(errors, parentKey = null) {
    const nonFieldErrors = [];

    for (const [key, value] of Object.entries(errors)) {
      if (key === 'nonFieldErrors' || key === 'non_field_errors') {
        const messages = Array.isArray(value) ? value : [value];
        for (const msg of messages) {
          nonFieldErrors.push([parentKey, msg]);
        }
      } else if (typeof value === 'object' && value !== null) {
        nonFieldErrors.push(...extractNonFieldErrors(value, key));
      }
    }

    return nonFieldErrors;
  }

  const nonFieldErrors = extractNonFieldErrors(errors);

  return (
    <ValidationErrorsProvider errors={Object.entries(errors)}>
      {nonFieldErrors && (
        <>
          {nonFieldErrors.map(([field, message], index) => (
            <ErrorMessage key={`${field}-${index}`}>{message}</ErrorMessage>
          ))}
        </>
      )}

      <div className="synchronize-variables-action-config">
        <Formik
          initialValues={{
            ...initialValues,
          }}
          onSubmit={values => onSave(values)}
        >
          {({values, setFieldValue, getFieldProps}) => (
            <Form>
              <Fieldset>
                <FormRow>
                  <Field
                    name="sourceVariable"
                    label={
                      <FormattedMessage
                        description="Synchronize variables modal select from variable field label"
                        defaultMessage="From variable"
                      />
                    }
                    required
                  >
                    <VariableSelection
                      {...getFieldProps('sourceVariable')}
                      name="sourceVariable"
                      value={values.sourceVariable}
                      filter={variable =>
                        variable.dataType === 'array' && variable.source === 'component'
                      }
                      onChange={e => {
                        const value = e.target.value;
                        const sourceComponent = components[value];
                        setFieldValue('sourceVariable', value);
                      }}
                    />
                  </Field>
                </FormRow>
                <FormRow>
                  <Field
                    name="destinationVariable"
                    label={
                      <FormattedMessage
                        description="Synchronize variables modal select to variable field label"
                        defaultMessage="To variable"
                      />
                    }
                    required
                  >
                    <VariableSelection
                      {...getFieldProps('destinationVariable')}
                      name="destinationVariable"
                      value={values.destinationVariable}
                      filter={variable =>
                        variable.dataType === 'array' && variable.source === 'component'
                      }
                      onChange={e => {
                        setFieldValue('destinationVariable', e.target.value);
                        setFieldValue('identifierVariable', '');
                        setFieldValue('dataMappings', []);
                      }}
                    />
                  </Field>
                </FormRow>

                <IdentifierVariable />
                <ManageDataMappings errors={errors} />
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

export {SynchronizeVariablesActionConfig};

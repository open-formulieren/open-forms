import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import {FormContext} from 'components/admin/form_design/Context';
import {getComponentDatatype} from 'components/admin/form_design/variables/utils';
import ActionButton, {SubmitAction} from 'components/admin/forms/ActionButton';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import ComponentSelection from 'components/admin/forms/ComponentSelection';
import {TextInput} from 'components/admin/forms/Inputs';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import {DeleteIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';
import {ChangelistTableWrapper, HeadColumn, TableRow} from 'components/admin/tables';

import {getErrorMarkup} from './utils';

const EMPTY_VARIABLE_PROPERTY = {
  propertyMappings: [{componentKey: '', eigenschap: ''}],
};

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

const VariableProperty = ({
  index,
  componentKey = '',
  eigenschap = '',
  componentFilterFunc,
  onChange,
  onDelete,
}) => {
  const intl = useIntl();

  const confirmDeleteMessage = intl.formatMessage({
    description: 'Delete confirmation message for variable mapped to case property',
    defaultMessage: 'Are you sure you want to remove this mapping?',
  });

  return (
    <TableRow index={index}>
      <div className="actions actions--horizontal actions--roomy">
        <DeleteIcon onConfirm={onDelete} message={confirmDeleteMessage} />
      </div>

      <ComponentSelection
        name="componentKey"
        value={componentKey}
        onChange={onChange}
        filter={componentFilterFunc}
      />
      <TextInput
        name="eigenschap"
        value={eigenschap}
        onChange={onChange}
        placeholder={componentKey}
      />
    </TableRow>
  );
};

VariableProperty.propTypes = {
  index: PropTypes.number.isRequired,
  componentKey: PropTypes.string,
  eigenschap: PropTypes.string,
  componentFilterFunc: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

const ManageVariableToPropertyMappings = ({propertyMappings = [], onChange, onAdd, onDelete}) => {
  const formContext = useContext(FormContext);
  const allComponents = formContext.components;

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

  const getSimpleComponentsLength = () => {
    const filteredComponents = Object.keys(allComponents).filter(comp => {
      const componentDataType = getComponentDatatype(allComponents[comp]);
      return !['array', 'object'].includes(componentDataType) && comp !== 'columns';
    });

    return filteredComponents.length;
  };

  return (
    <>
      <ChangelistTableWrapper headColumns={<HeadColumns />}>
        {propertyMappings.map((mappedVariable, index) => (
          <VariableProperty
            key={index}
            index={index}
            componentFilterFunc={filterFunc.bind(null, mappedVariable.componentKey)}
            onChange={onChange.bind(null, index)}
            onDelete={onDelete.bind(null, index)}
            {...mappedVariable}
          />
        ))}
      </ChangelistTableWrapper>

      {usedComponents.length < getSimpleComponentsLength() ? (
        <ButtonContainer onClick={onAdd}>
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
  );
};

ManageVariableToPropertyMappings.propTypes = {
  propertyMappings: PropTypes.arrayOf(
    PropTypes.shape({
      componentKey: PropTypes.string,
      eigenschap: PropTypes.string,
    })
  ).isRequired,
  onChange: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

const VariablePropertyModal = ({index, name, formData, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const validationErrors = useContext(ValidationErrorContext);

  const {propertyMappings = []} = formData;

  const onAddVariableProperty = () => {
    const nextFormData = produce(formData, draft => {
      if (!draft.propertyMappings) draft.propertyMappings = [];
      draft.propertyMappings.push(EMPTY_VARIABLE_PROPERTY);
    });
    onChange(nextFormData);
  };

  const onChangeVariableProperty = (index, event) => {
    const {name, value} = event.target;
    const nextFormData = produce(formData, draft => {
      draft.propertyMappings[index][name] = value;
    });
    onChange(nextFormData);
  };

  const onDeleteVariableProperty = index => {
    const nextFormData = produce(formData, draft => {
      draft.propertyMappings.splice(index, 1);
    });
    onChange(nextFormData);
  };

  /**
   * Handle property mappings errors and show them to the main page, not inside the modal.
   */
  const getCombinedErrors = (name, index, errors) => {
    const errorMessages = [];

    for (const [errorName, errorReason] of errors) {
      if (errorName.startsWith(name + '.propertyMappings')) {
        const errorNameBits = errorName.split('.');
        const lastNameBit = errorNameBits[errorNameBits.length - 1];

        if (errorNameBits[2] === String(index)) {
          // Custom error in validate method from the API call
          if (lastNameBit === 'propertyMappings') {
            errorMessages.push(errorReason);
          } else {
            // Errors raised from the serializer's definition
            if (lastNameBit === 'componentKey') {
              errorMessages.push('Component key: ' + errorReason);
            } else if (lastNameBit === 'eigenschap') {
              errorMessages.push('Property: ' + errorReason);
            }
          }
        }
      }
    }

    return errorMessages.length > 0 ? errorMessages : null;
  };

  return (
    <>
      <CustomFieldTemplate
        id="zgwOptions.managePropertiesVariables"
        displayLabel={false}
        rawErrors={getCombinedErrors(name, index, validationErrors)}
        errors={
          getCombinedErrors(name, index, validationErrors)
            ? getErrorMarkup(getCombinedErrors(name, index, validationErrors))
            : null
        }
      >
        <ActionButton
          text={intl.formatMessage({
            description: 'Open map case properties to variables modal button',
            defaultMessage: 'Map variables to case properties',
          })}
          type="button"
          onClick={() => setModalOpen(!modalOpen)}
        />
        &nbsp;
        <FormattedMessage
          description="Managed mappings state feedback"
          defaultMessage="{varCount, plural,
                            =0 {}
                            one {(1 variable mapped)}
                            other {({varCount} variables mapped)}
                        }"
          values={{varCount: propertyMappings.length}}
        />
      </CustomFieldTemplate>

      <FormModal
        isOpen={modalOpen}
        title={
          <FormattedMessage
            description="Modal title for case property to variable mapping"
            defaultMessage="Map variables to case properties"
          />
        }
        closeModal={() => setModalOpen(false)}
      >
        <ManageVariableToPropertyMappings
          propertyMappings={propertyMappings}
          onChange={onChangeVariableProperty}
          onAdd={onAddVariableProperty}
          onDelete={onDeleteVariableProperty}
        />
        <SubmitRow>
          <SubmitAction
            text={intl.formatMessage({
              description: 'Confirm button for case property to variable mapping',
              defaultMessage: 'Confirm',
            })}
            onClick={event => {
              event.preventDefault();
              setModalOpen(false);
            }}
          />
        </SubmitRow>
      </FormModal>
    </>
  );
};

VariablePropertyModal.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
  formData: PropTypes.shape({
    contentJson: PropTypes.string,
    informatieobjecttype: PropTypes.string,
    medewerkerRoltype: PropTypes.string,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    organisatieRsin: PropTypes.string,
    propertyMappings: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenschap: PropTypes.string,
      })
    ).isRequired,
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    zaaktype: PropTypes.string,
    zgwApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  onChange: PropTypes.func.isRequired,
};

export {VariablePropertyModal};

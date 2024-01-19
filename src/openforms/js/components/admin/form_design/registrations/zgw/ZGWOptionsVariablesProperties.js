import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import {FormContext} from 'components/admin/form_design/Context';
import {getComponentDatatype} from 'components/admin/form_design/variables/utils';
import ActionButton, {SubmitAction} from 'components/admin/forms/ActionButton';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import ComponentSelection from 'components/admin/forms/ComponentSelection';
import {TextInput} from 'components/admin/forms/Inputs';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import {FormModal} from 'components/admin/modals';
import {ChangelistTableWrapper, HeadColumn, TableRow} from 'components/admin/tables';

import {getErrorMarkup} from './utils';

const EMPTY_VARIABLE_PROPERTY = {
  variablesProperties: [{componentKey: '', eigenshap: ''}],
};

const HeadColumns = () => {
  const intl = useIntl();

  const componentText = intl.formatMessage({
    description: 'Manage component column title',
    defaultMessage: 'Variable',
  });
  const componentHelp = intl.formatMessage({
    description: 'Manage component help text',
    defaultMessage: 'The value of the selected field will be the process variable value.',
  });

  const eigenshapText = intl.formatMessage({
    description: 'Manage property column title',
    defaultMessage: 'Property',
  });

  const eigenshapHelp = intl.formatMessage({
    description: 'Manage property help text',
    defaultMessage: 'Specify a ZGW property name.',
  });

  return (
    <>
      <HeadColumn content="" />
      <HeadColumn content={componentText} title={componentHelp} />
      <HeadColumn content={eigenshapText} title={eigenshapHelp} />
    </>
  );
};

const VariableProperty = ({
  index,
  componentKey = '',
  eigenshap = '',
  componentFilterFunc,
  onChange,
  onDelete,
}) => {
  const intl = useIntl();

  const confirmDeleteMessage = intl.formatMessage({
    description: 'ZGW properties with variables connection delete confirmation message',
    defaultMessage: 'Are you sure you want to remove this connection?',
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
        filter={componentFilterFunc.bind(null, componentKey)}
      />
      <TextInput
        name="eigenshap"
        value={eigenshap}
        onChange={onChange}
        placeholder={componentKey}
      />
    </TableRow>
  );
};

VariableProperty.propTypes = {
  index: PropTypes.number.isRequired,
  componentKey: PropTypes.string,
  eigenshap: PropTypes.string,
  componentFilterFunc: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

const SelectVariablesProperties = ({variablesProperties = [], onChange, onAdd, onDelete}) => {
  const formContext = useContext(FormContext);
  const allComponents = formContext.components;

  const usedComponents = variablesProperties
    .filter(connection => connection.componentKey !== '')
    .map(connection => connection.componentKey);

  const filterFunc = (componentKey, component) => {
    const isSimpleType = !['array', 'object'].includes(getComponentDatatype(component));
    const componentNotUsed =
      componentKey === component.key || !usedComponents.includes(component.key);

    return isSimpleType && componentNotUsed;
  };

  const getSimpleComponentsLength = () => {
    const filteredComponents = [];

    for (const comp in allComponents) {
      if (!['array', 'object'].includes(getComponentDatatype(allComponents[comp]))) {
        filteredComponents.push(comp);
      }
    }
    return filteredComponents.length;
  };

  return (
    <>
      <ChangelistTableWrapper headColumns={<HeadColumns />}>
        {variablesProperties.map((processVar, index) => (
          <VariableProperty
            key={index}
            index={index}
            componentFilterFunc={filterFunc}
            onChange={onChange.bind(null, index)}
            onDelete={onDelete.bind(null, index)}
            {...processVar}
          />
        ))}
      </ChangelistTableWrapper>

      {usedComponents.length < getSimpleComponentsLength() ? (
        <ButtonContainer onClick={onAdd}>
          <FormattedMessage
            description="Add process variable button"
            defaultMessage="Add variable"
          />
        </ButtonContainer>
      ) : null}
    </>
  );
};

SelectVariablesProperties.propTypes = {
  variablesProperties: PropTypes.arrayOf(
    PropTypes.shape({
      componentKey: PropTypes.string,
      eigenshap: PropTypes.string,
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

  const {variablesProperties = []} = formData;

  const onAddVariableProperty = () => {
    const nextFormData = produce(formData, draft => {
      if (!draft.variablesProperties) draft.variablesProperties = [];
      draft.variablesProperties.push(EMPTY_VARIABLE_PROPERTY);
    });
    onChange(nextFormData);
  };

  const onChangeVariableProperty = (index, event) => {
    const {name, value} = event.target;
    const nextFormData = produce(formData, draft => {
      draft.variablesProperties[index][name] = value;
    });
    onChange(nextFormData);
  };

  const onDeleteVariableProperty = index => {
    const nextFormData = produce(formData, draft => {
      draft.variablesProperties.splice(index, 1);
    });
    onChange(nextFormData);
  };

  /**
   * Handle variables-properties errors and show them to the main page, not inside the modal.
   */
  const getCombinedErrors = (name, index, errors) => {
    const errorMessages = [];

    for (const [errorName, errorReason] of errors) {
      if (errorName.startsWith(name + '.variablesProperties')) {
        const errorNameBits = errorName.split('.');
        if (errorNameBits[2] === String(index))
          if (errorNameBits[errorNameBits.length - 1] === 'componentKey') {
            errorMessages.push('Component key: ' + errorReason);
          } else if (errorNameBits[errorNameBits.length - 1] === 'eigenshap') {
            errorMessages.push('Property: ' + errorReason);
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
            description: 'Open connect ZGW properties with variables modal button',
            defaultMessage: 'Connect variables with ZAAK properties',
          })}
          type="button"
          onClick={() => setModalOpen(!modalOpen)}
        />
        &nbsp;
        <FormattedMessage
          description="Managed connections state feedback"
          defaultMessage="{varCount, plural,
                            =0 {}
                            one {(1 variable mapped)}
                            other {({varCount} variables mapped)}
                        }"
          values={{varCount: variablesProperties.length}}
        />
      </CustomFieldTemplate>

      <FormModal
        isOpen={modalOpen}
        title={
          <FormattedMessage
            description="ZGW properties with variables connection modal title"
            defaultMessage="Connect variables with ZAAK properties"
          />
        }
        closeModal={() => setModalOpen(false)}
      >
        <SelectVariablesProperties
          variablesProperties={variablesProperties}
          onChange={onChangeVariableProperty}
          onAdd={onAddVariableProperty}
          onDelete={onDeleteVariableProperty}
        />
        <SubmitRow>
          <SubmitAction
            text={intl.formatMessage({
              description: 'ZGW properties with variables connection confirm button',
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
    variablesProperties: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenshap: PropTypes.string,
      })
    ).isRequired,
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    zaaktype: PropTypes.string,
    zgwApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  onChange: PropTypes.func.isRequired,
};

export {VariablePropertyModal};

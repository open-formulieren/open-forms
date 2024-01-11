import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import ActionButton, {SubmitAction} from 'components/admin/forms/ActionButton';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import ComponentSelection from 'components/admin/forms/ComponentSelection';
import {TextInput} from 'components/admin/forms/Inputs';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';
import {ChangelistTableWrapper, HeadColumn, TableRow} from 'components/admin/tables';

const EMPTY_VARIABLE_PROPERTY = {
  variablesProperties: [{componentKey: '', eigenshap: ''}],
};

const HeadColumns = () => {
  const intl = useIntl();

  const componentText = (
    <FormattedMessage description="Manage component column title" defaultMessage="Variable" />
  );
  const componentHelp = intl.formatMessage({
    description: 'Manage component help text',
    defaultMessage: 'The value of the selected field will be the process variable value.',
  });

  const eigenshapText = (
    <FormattedMessage description="Manage property column title" defaultMessage="Property" />
  );
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
  const usedComponents = variablesProperties
    .filter(variable => variable.componentKey !== '')
    .map(variable => variable.componentKey);

  const filterFunc = (componentKey, {key}) => componentKey === key || !usedComponents.includes(key);

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

      <ButtonContainer onClick={onAdd}>
        <FormattedMessage description="Add process variable button" defaultMessage="Add variable" />
      </ButtonContainer>
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

const VariablePropertyModal = ({formData, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);

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

  return (
    <>
      <CustomFieldTemplate
        id="zgwOptions.managePropertiesVariables"
        displayLabel={false}
        rawErrors={null}
        errors={null}
      >
        <ActionButton
          text={intl.formatMessage({
            description: 'Open connect ZGW properties with variables modal button',
            defaultMessage: 'Connect variables with ZGW properties',
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
            defaultMessage="Connect variables with ZGW properties"
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

import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import FAIcon from 'components/admin/FAIcon';
import FormModal from 'components/admin/FormModal';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {SubmitAction} from 'components/admin/forms/ActionButton';
import Select from 'components/admin/forms/Select';
import SubmitRow from 'components/admin/forms/SubmitRow';

import {FormContext} from './Context';

const NewStepFormDefinitionPicker = ({onReplace}) => {
  const intl = useIntl();
  const formContext = useContext(FormContext);
  const formDefinitions = formContext.formDefinitions;
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedFormDefinition, setSelectedFormDefinition] = useState('');
  const [validationErrors, setValidationErrors] = useState([]);

  const formDefinitionChoices = formDefinitions
    .filter(fd => fd.isReusable)
    .map(fd => [fd.url, fd.internalName || fd.name]);

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const onFormDefinitionConfirmed = event => {
    event.preventDefault();
    if (!selectedFormDefinition) {
      const requiredError = intl.formatMessage({
        description: 'Field required error',
        defaultMessage: 'This field is required.',
      });
      setValidationErrors([requiredError]);
    } else {
      closeModal();
      onReplace(selectedFormDefinition);
    }
  };

  const onSelectChange = event => {
    const {
      target: {value},
    } = event;
    setValidationErrors([]);
    setSelectedFormDefinition(value);
  };

  return (
    <div className="tiles tiles--horizontal">
      <button type="button" className="tiles__tile" onClick={() => setIsModalOpen(true)}>
        <FAIcon
          icon="recycle"
          extraClassname="fa-2x"
          title={intl.formatMessage({
            description: 'select definition icon title',
            defaultMessage: 'Select definition',
          })}
        />
        <span>
          <FormattedMessage
            description="Select form definition tile"
            defaultMessage="Select existing form definition"
          />
        </span>
      </button>

      <span className="tiles__separator">&bull;</span>

      <button
        type="button"
        className="tiles__tile"
        onClick={() => {
          onReplace('');
        }}
      >
        <FAIcon
          icon="pen-to-square"
          extraClassname="fa-2x"
          title={intl.formatMessage({
            description: 'create form definition icon title',
            defaultMessage: 'Create definition',
          })}
        />
        <span>
          <FormattedMessage
            description="Create form definition tile"
            defaultMessage="Create a new form definition"
          />
        </span>
      </button>

      <FormModal
        isOpen={isModalOpen}
        closeModal={closeModal}
        title={
          <FormattedMessage
            description="Form definition selection modal title"
            defaultMessage="Use existing form definition"
          />
        }
      >
        <FormRow>
          <Field
            name="form-definition"
            label={
              <FormattedMessage
                description="Form definition select label"
                defaultMessage="Select form definition"
              />
            }
            errors={validationErrors}
            required
          >
            <Select
              name="form-definition"
              choices={formDefinitionChoices}
              value={selectedFormDefinition}
              onChange={onSelectChange}
              allowBlank
            />
          </Field>
        </FormRow>

        <SubmitRow isDefault>
          <SubmitAction
            text={intl.formatMessage({
              description: 'Form definition select confirm button',
              defaultMessage: 'Confirm',
            })}
            onClick={onFormDefinitionConfirmed}
          />
        </SubmitRow>
      </FormModal>
    </div>
  );
};

NewStepFormDefinitionPicker.propTypes = {
  onReplace: PropTypes.func.isRequired,
};

export default NewStepFormDefinitionPicker;

import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import JsonWidget from 'components/admin/forms/JsonWidget';
import MappingArrayInput from 'components/admin/forms/MappingArrayInput';
import Select from 'components/admin/forms/Select';
import SubmitRow from 'components/admin/forms/SubmitRow';

import {FormLogicContext} from '../Context';

const HTTP_METHODS = [
  ['GET', 'GET'],
  ['POST', 'POST'],
];
const EXPRESSION_MAPPING_LANGUAGES = [
  ['JsonLogic', 'JsonLogic'],
  ['jq', 'jq'],
];

const ServiceFetchConfigurationForm = ({
  stateData = {},
  selectExisting = false,
  setData,
  onFormSave,
}) => {
  // TODO ensure that onChange actually updates state with data
  const intl = useIntl();
  const formLogicContext = useContext(FormLogicContext);
  // const [stateData, setData] = useState(data);

  const onChange = event => {
    const [prefix, key] = event.target.name.split('.');
    let copiedData = Object.assign({}, stateData);
    copiedData[key] = event.target.value;
    setData(copiedData);
  };

  const serviceChoices = formLogicContext.services.map(service => {
    return [service.url, service.label];
  });

  return (
    <div>
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Basic"
            description="Service fetch configuration modal basic fieldset title"
          />
        }
        extraClassName="admin-fieldset"
      >
        <FormRow>
          <Field
            name={'fetchConfiguration.service'}
            label={
              <FormattedMessage
                defaultMessage="Service"
                description="Service fetch configuration modal form Service field label"
              />
            }
          >
            <Select
              name="fetchConfiguration.httpMethod"
              choices={serviceChoices}
              value={stateData.service}
              onChange={onChange}
            />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name={'fetchConfiguration.path'}
            label={
              <FormattedMessage
                defaultMessage="Path"
                description="Service fetch configuration modal form Path field label"
              />
            }
          >
            <TextInput value={stateData.path} onChange={onChange} maxLength="1000" />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name={'fetchConfiguration.method'}
            label={
              <FormattedMessage
                defaultMessage="HTTP method"
                description="Service fetch configuration modal form HTTP method field label"
              />
            }
          >
            <Select
              name="fetchConfiguration.method"
              choices={HTTP_METHODS}
              value={stateData.method || 'GET'}
              onChange={onChange}
            />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name={'fetchConfiguration.queryParams'}
            label={
              <FormattedMessage
                defaultMessage="Query parameters"
                description="Service fetch configuration modal form query parameters field label"
              />
            }
          >
            <MappingArrayInput
              name="fetchConfiguration.queryParams"
              valueArrayInput={true}
              onChange={({...args}) => {
                null;
              }}
            />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name={'fetchConfiguration.headers'}
            label={
              <FormattedMessage
                defaultMessage="Request headers"
                description="Service fetch configuration modal form request headers field label"
              />
            }
          >
            <MappingArrayInput
              name="fetchConfiguration.headers"
              onChange={({...args}) => {
                null;
              }}
            />
          </Field>
        </FormRow>

        {stateData.method === 'POST' ? (
          <FormRow>
            <Field
              name={'fetchConfiguration.body'}
              label={
                <FormattedMessage
                  defaultMessage="Request body"
                  description="Service fetch configuration modal form request body field label"
                />
              }
            >
              <JsonWidget
                name="fetchConfiguration.body"
                logic={stateData.body || {}}
                cols={20}
                onChange={onChange}
              />
            </Field>
          </FormRow>
        ) : null}

        <FormRow>
          <Field
            name={'fetchConfiguration.dataMappingType'}
            label={
              <FormattedMessage
                defaultMessage="Mapping expression language"
                description="Service fetch configuration modal form mapping expression language field label"
              />
            }
          >
            <Select
              name="fetchConfiguration.dataMappingType"
              choices={EXPRESSION_MAPPING_LANGUAGES}
              value={stateData.dataMappingType || ''}
              onChange={onChange}
              allowBlank
            />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name={'fetchConfiguration.mappingExpression'}
            label={
              <FormattedMessage
                defaultMessage="Mapping expression"
                description="Service fetch configuration modal form mapping expression field label"
              />
            }
          >
            <JsonWidget
              name="fetchConfiguration.mappingExpression"
              logic={stateData.mappingExpression || {}}
              cols={20}
              onChange={onChange}
            />
          </Field>
        </FormRow>
      </Fieldset>

      <SubmitRow>
        <button type="button" className="button" onClick={onFormSave}>
          <FormattedMessage description="Save service fetch configuration" defaultMessage="Save" />
        </button>

        {selectExisting ? (
          <button type="button" className="button" onClick={onFormSave}>
            <FormattedMessage
              description="Copy and save service fetch configuration"
              defaultMessage="Copy and save"
            />
          </button>
        ) : null}
      </SubmitRow>
    </div>
  );
};

ServiceFetchConfigurationForm.propTypes = {
  onFormSubmit: PropTypes.func,
};

export default ServiceFetchConfigurationForm;

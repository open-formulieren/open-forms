import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

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
  const intl = useIntl();
  const formLogicContext = useContext(FormLogicContext);
  // const [stateData, setData] = useState(data);

  const onChange = event => {
    if (!event.target) return;
    const [prefix, key] = event.target.name.split('.');
    let copiedData = Object.assign({}, stateData);
    copiedData[key] = event.target.value;
    setData(copiedData);
  };

  const onMappingChange = (key, value) => {
    let copiedData = Object.assign({}, stateData);
    copiedData[key] = value;
    setData(copiedData);
  };

  const serviceChoices = [['', '-------']].concat(
    formLogicContext.services.map(service => {
      return [service.url, service.label];
    })
  );

  const queryString = new URLSearchParams(stateData.queryParams || {}).toString();

  return (
    <div>
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Preview"
            description="Service fetch configuration modal preview fieldset title"
          />
        }
        extraClassName="admin-fieldset"
      >
        <FormRow>
          <Field
            name={'fetchConfiguration.preview'}
            label={
              <FormattedMessage
                defaultMessage="Request preview"
                description="Service fetch configuration modal form request preview field label"
              />
            }
          >
            <div>
              <span className="servicefetchconfiguration-form__preview">
                {stateData.method || 'GET'} {stateData.service}
                {stateData.path}
                {queryString !== '' ? `?${queryString}` : null}
              </span>
              {stateData.headers ? (
                <table>
                  <thead>
                    <tr>
                      <th>Header key</th>
                      <th>Header value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stateData.headers.map(([key, value], index) => {
                      if (key === '') return null;
                      else
                        return (
                          <tr key={key}>
                            <td>{key}</td>
                            <td>{value}</td>
                          </tr>
                        );
                    })}
                  </tbody>
                </table>
              ) : null}
            </div>
          </Field>
        </FormRow>
      </Fieldset>

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
              name="fetchConfiguration.method"
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
            <TextInput value={stateData.path || ''} onChange={onChange} maxLength="1000" />
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
              mapping={stateData.queryParams}
              valueArrayInput={true}
              onChange={onMappingChange}
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
              mapping={stateData.headers}
              onChange={onMappingChange}
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
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Data extraction"
            description="Service fetch configuration modal data extraction fieldset title"
          />
        }
        extraClassName="admin-fieldset"
      >
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
            {stateData.dataMappingType === 'JsonLogic' ? (
              <JsonWidget
                name="fetchConfiguration.mappingExpression"
                logic={stateData.mappingExpression || {}}
                cols={20}
                onChange={onChange}
              />
            ) : (
              <TextInput value={stateData.mappingExpression} onChange={onChange} />
            )}
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

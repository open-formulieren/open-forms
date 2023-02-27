import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import ActionButton from 'components/admin/forms/ActionButton';
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

  return (
    <div>
      <Tabs>
        <TabList>
          <Tab key="configuration">
            <FormattedMessage
              description="Service fetch config configuration tab title"
              defaultMessage="Configuration"
            />
          </Tab>

          <Tab key="try-it-out">
            <FormattedMessage
              description="Service fetch config try it out tab title"
              defaultMessage="Try it out"
            />
          </Tab>
        </TabList>

        <TabPanel key="configuration">
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
                name={'fetchConfiguration.method'}
                required
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
                name={'fetchConfiguration.service'}
                fieldBox
                required
                label={
                  <FormattedMessage
                    defaultMessage="Service"
                    description="Service fetch configuration modal form Service field label"
                  />
                }
              >
                <Select
                  name="fetchConfiguration.service"
                  choices={serviceChoices}
                  value={stateData.service}
                  onChange={onChange}
                />
              </Field>
              <Field
                name={'fetchConfiguration.path'}
                fieldBox
                required
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
                required
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
                required
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
                  <TextInput
                    // Explicitly cast object to strings, in case the JsonWidget was used before
                    value={
                      typeof stateData.mappingExpression === 'object'
                        ? JSON.stringify(stateData.mappingExpression)
                        : stateData.mappingExpression
                    }
                    onChange={onChange}
                  />
                )}
              </Field>
            </FormRow>
          </Fieldset>
        </TabPanel>

        <TabPanel key="try-it-out">
          <Fieldset
            title={
              <FormattedMessage
                defaultMessage="Full request"
                description="Service fetch configuration try it out tabpanel full request fieldset title"
              />
            }
            extraClassName="admin-fieldset"
          >
            <FormRow>
              {/* TODO https://github.com/open-formulieren/open-forms/issues/2777 */}
              {/* should contain inputs for the user to provide values */}
              {/* for variable interpolation and a button to fire the request */}
              {/* as a result, it should display the value as extracted using the mapping expression */}
              <Field>
                <span>...</span>
              </Field>
            </FormRow>
          </Fieldset>
          <Fieldset
            title={
              <FormattedMessage
                defaultMessage="Data extraction"
                description="Service fetch configuration try it out tabpanel data extraction fieldset title"
              />
            }
            extraClassName="admin-fieldset"
          >
            <FormRow>
              {/* TODO https://github.com/open-formulieren/open-forms/issues/2777 */}
              {/* should contain an input for the user to provide a JSON blob */}
              {/* and a button to apply the mapping expression to this data */}
              {/* as a result, it should display the value as extracted using the mapping expression */}
              <Field>
                <span>...</span>
              </Field>
            </FormRow>
          </Fieldset>
        </TabPanel>
      </Tabs>

      <SubmitRow>
        {selectExisting ? (
          <>
            <ActionButton
              name="_save_as_new"
              text={intl.formatMessage({
                description: 'Save as new service fetch configuration button label',
                defaultMessage: 'Save as new',
              })}
              onClick={onFormSave}
            />
            <ActionButton
              name="_save_config"
              text={intl.formatMessage({
                description: 'Update service fetch configuration button label',
                defaultMessage: 'Update',
              })}
              onClick={onFormSave}
            />
          </>
        ) : (
          <ActionButton
            name="_save_config"
            text={intl.formatMessage({
              description: 'Save service fetch configuration button label',
              defaultMessage: 'Save',
            })}
            onClick={onFormSave}
          />
        )}
      </SubmitRow>
    </div>
  );
};

ServiceFetchConfigurationForm.propTypes = {
  onFormSubmit: PropTypes.func,
};

export default ServiceFetchConfigurationForm;

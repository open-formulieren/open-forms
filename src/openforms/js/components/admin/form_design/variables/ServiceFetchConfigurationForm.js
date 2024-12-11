import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import ActionButton from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {NumberInput, TextInput} from 'components/admin/forms/Inputs';
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

const ServiceFetchConfigurationForm = ({formik, selectExisting = false}) => {
  const intl = useIntl();
  const formLogicContext = useContext(FormLogicContext);

  const serviceChoices = formLogicContext.services.map(service => {
    return [service.url, service.label];
  });

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
          >
            <FormRow>
              <Field
                name="name"
                fieldBox
                required
                label={
                  <FormattedMessage
                    defaultMessage="Name"
                    description="Service fetch configuration modal form name field label"
                  />
                }
              >
                <TextInput id="name" maxLength="1000" {...formik.getFieldProps('name')} />
              </Field>
            </FormRow>

            <FormRow>
              <Field
                name="method"
                required
                label={
                  <FormattedMessage
                    defaultMessage="HTTP method"
                    description="Service fetch configuration modal form HTTP method field label"
                  />
                }
              >
                <Select
                  id="method"
                  choices={HTTP_METHODS}
                  value={formik.values.method}
                  {...formik.getFieldProps('method')}
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field
                name="service"
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
                  id="service"
                  choices={serviceChoices}
                  value={formik.values.service}
                  {...formik.getFieldProps('service')}
                  allowBlank
                />
              </Field>
              <Field
                name="path"
                fieldBox
                required
                label={
                  <FormattedMessage
                    defaultMessage="Path"
                    description="Service fetch configuration modal form Path field label"
                  />
                }
                helpText={
                  <FormattedMessage
                    defaultMessage="the path should not have a leading slash"
                    description="Service fetch configuration modal form Path field help text"
                  />
                }
              >
                <TextInput
                  id="path"
                  value={formik.values.path}
                  maxLength="1000"
                  {...formik.getFieldProps('path')}
                />
              </Field>
            </FormRow>

            <FormRow>
              <Field
                name="cacheTimeout"
                fieldBox
                required={false}
                label={
                  <FormattedMessage
                    defaultMessage="Cache timeout"
                    description="Label cache timeout"
                  />
                }
                helpText={
                  <FormattedMessage
                    defaultMessage="After how many seconds should the cached response expire."
                    description="Help text cache timeout"
                  />
                }
              >
                <NumberInput
                  id="cacheTimeout"
                  value={formik.values.cacheTimeout ?? ''}
                  {...formik.getFieldProps('cacheTimeout')}
                />
              </Field>
            </FormRow>

            <FormRow fields={['queryParams']}>
              <Field
                name="queryParams"
                label={
                  <FormattedMessage
                    defaultMessage="Query parameters"
                    description="Service fetch configuration modal form query parameters field label"
                  />
                }
              >
                <MappingArrayInput
                  name="queryParams"
                  mapping={formik.values.queryParams}
                  valueArrayInput={true}
                  {...formik.getFieldProps('queryParams')}
                  inputType="text"
                />
              </Field>
            </FormRow>

            <FormRow fields={['headers']}>
              <Field
                name="headers"
                label={
                  <FormattedMessage
                    defaultMessage="Request headers"
                    description="Service fetch configuration modal form request headers field label"
                  />
                }
              >
                <MappingArrayInput
                  name="headers"
                  mapping={formik.values.headers}
                  {...formik.getFieldProps('headers')}
                  inputType="text"
                />
              </Field>
            </FormRow>

            {formik.values.method === 'POST' ? (
              <FormRow>
                <Field
                  name="body"
                  label={
                    <FormattedMessage
                      defaultMessage="Request body"
                      description="Service fetch configuration modal form request body field label"
                    />
                  }
                >
                  <JsonWidget
                    name="body"
                    logic={formik.values.body}
                    cols={50}
                    onChange={formik.getFieldProps('body').onChange}
                    testid="request-body"
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
          >
            <FormRow>
              <Field
                name="dataMappingType"
                required
                label={
                  <FormattedMessage
                    defaultMessage="Mapping expression language"
                    description="Service fetch configuration modal form mapping expression language field label"
                  />
                }
              >
                <Select
                  name="dataMappingType"
                  choices={EXPRESSION_MAPPING_LANGUAGES}
                  value={formik.values.dataMappingType}
                  allowBlank
                  {...formik.getFieldProps('dataMappingType')}
                />
              </Field>
            </FormRow>

            {formik.values.dataMappingType === 'JsonLogic' ? (
              <FormRow>
                <Field
                  name="jsonLogicExpression"
                  required
                  label={
                    <FormattedMessage
                      defaultMessage="Mapping expression"
                      description="Service fetch configuration modal form mapping expression field label"
                    />
                  }
                >
                  <JsonWidget
                    name="jsonLogicExpression"
                    logic={formik.values.jsonLogicExpression || ''}
                    cols={50}
                    onChange={formik.getFieldProps('jsonLogicExpression').onChange}
                    testid="mapping-expression-json-logic"
                  />
                </Field>
              </FormRow>
            ) : (
              <FormRow>
                <Field
                  name="jqExpression"
                  required
                  label={
                    <FormattedMessage
                      defaultMessage="Mapping expression"
                      description="Service fetch configuration modal form mapping expression field label"
                    />
                  }
                >
                  <TextInput name="jqExpression" {...formik.getFieldProps('jqExpression')} />
                </Field>
              </FormRow>
            )}
          </Fieldset>

          <SubmitRow>
            {selectExisting ? (
              <>
                <ActionButton
                  name="_save_as_new"
                  text={intl.formatMessage({
                    description: 'Save as new service fetch configuration button label',
                    defaultMessage: 'Save as new',
                  })}
                  onClick={e => {
                    // Remove ID to ensure that new entry is created
                    formik.setFieldValue('id', null);
                    return formik.handleSubmit(e);
                  }}
                  type="submit"
                />
                <ActionButton
                  name="_save_config"
                  text={intl.formatMessage({
                    description: 'Update service fetch configuration button label',
                    defaultMessage: 'Update',
                  })}
                  onClick={formik.handleSubmit}
                />
              </>
            ) : (
              <ActionButton
                name="_save_config"
                text={intl.formatMessage({
                  description: 'Save service fetch configuration button label',
                  defaultMessage: 'Save',
                })}
                onClick={formik.handleSubmit}
                type="submit"
              />
            )}
          </SubmitRow>
        </TabPanel>

        <TabPanel key="try-it-out">
          <Fieldset
            title={
              <FormattedMessage
                defaultMessage="Full request"
                description="Service fetch configuration try it out tabpanel full request fieldset title"
              />
            }
          >
            <FormRow>
              {/* TODO https://github.com/open-formulieren/open-forms/issues/2777 */}
              {/* should contain inputs for the user to provide values */}
              {/* for variable interpolation and a button to fire the request */}
              {/* as a result, it should display the value as extracted using the mapping expression */}
              <Field name="full-request-preview">
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
          >
            <FormRow>
              {/* TODO https://github.com/open-formulieren/open-forms/issues/2777 */}
              {/* should contain an input for the user to provide a JSON blob */}
              {/* and a button to apply the mapping expression to this data */}
              {/* as a result, it should display the value as extracted using the mapping expression */}
              <Field name="data-extraction-preview">
                <span>...</span>
              </Field>
            </FormRow>
          </Fieldset>
        </TabPanel>
      </Tabs>
    </div>
  );
};

ServiceFetchConfigurationForm.propTypes = {
  formik: PropTypes.object,
  selectExisting: PropTypes.bool,
};

export default ServiceFetchConfigurationForm;

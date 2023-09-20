import {useFormik} from 'formik';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

import {FormLogicContext} from '../Context';
import ServiceFetchConfigurationForm from './ServiceFetchConfigurationForm';

const INITIAL_VALUES = {
  id: null,
  name: '',
  method: 'GET',
  service: '',
  path: '',
  queryParams: [],
  headers: [],
  body: null,
  dataMappingType: '',
  mappingExpression: '',
  // These fields are mapped to mappingExpression on save
  jsonLogicExpression: {},
  jqExpression: '',
  cacheTimeout: null,
};

const ServiceFetchConfigurationPicker = ({
  initialValues = INITIAL_VALUES,
  variableName,
  onChange,
  onFormSave,
}) => {
  const formLogicContext = useContext(FormLogicContext);

  const [selectExisting, setSelectExisting] = useState(!!initialValues.id);
  const [selectedServiceFetchConfig, setSelectedServiceFetchConfig] = useState(initialValues.id);

  const serviceFetchConfigurationChoices = formLogicContext.serviceFetchConfigurations.map(
    fetchConfig => {
      return [
        fetchConfig.id,
        fetchConfig.name || `${fetchConfig.method} ${fetchConfig.path} (${fetchConfig.service})`,
      ];
    }
  );

  const formik = useFormik({
    initialValues: initialValues,
    onSubmit: (values, {setSubmitting}) => {
      switch (values.dataMappingType) {
        case 'JsonLogic':
          values.mappingExpression = values.jsonLogicExpression;
          break;
        case 'jq':
          values.mappingExpression = values.jqExpression;
          break;
        default:
          values.mappingExpression = values.jqExpression;
      }
      delete values.jsonLogicExpression;
      delete values.jqExpression;

      formLogicContext.onServiceFetchAdd(variableName, values);
      onFormSave();
      setSubmitting(false);
    },
  });

  return (
    <div className="servicefetchconfiguration-picker">
      <div className="servicefetchconfiguration-select">
        <FormRow>
          <Field
            name="fetchConfiguration.existing"
            label={
              <FormattedMessage
                defaultMessage="Choose existing configuration"
                description="Service fetch configuration modal select existing field label"
              />
            }
          >
            <Select
              choices={serviceFetchConfigurationChoices}
              value={selectedServiceFetchConfig}
              onChange={event => {
                onChange(event);
                setSelectedServiceFetchConfig(event.target.value);

                const values =
                  _.cloneDeep(
                    formLogicContext.serviceFetchConfigurations.find(
                      element => element.id === parseInt(event.target.value)
                    )
                  ) || _.cloneDeep(formik.initialValues);

                switch (values.dataMappingType) {
                  case 'JsonLogic':
                    values.jsonLogicExpression = values.mappingExpression;
                    break;
                  case 'jq':
                    values.jqExpression = values.mappingExpression;
                    break;
                  default:
                    values.jqExpression = values.mappingExpression;
                }

                formik.setValues(values);

                setSelectExisting(!!event.target.value);
              }}
              allowBlank
            />
          </Field>
        </FormRow>
      </div>

      <form className="servicefetchconfiguration-form" onSubmit={formik.handleSubmit}>
        <ServiceFetchConfigurationForm formik={formik} selectExisting={selectExisting} />
      </form>
    </div>
  );
};

ServiceFetchConfigurationPicker.propTypes = {
  variableName: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onFormSave: PropTypes.func.isRequired,
  initialValues: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    name: PropTypes.string.isRequired,
    method: PropTypes.oneOf(['GET', 'POST']),
    service: PropTypes.string.isRequired,
    path: PropTypes.string.isRequired,
    queryParams: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.array), PropTypes.object])
      .isRequired,
    headers: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.array), PropTypes.object]).isRequired,
    body: PropTypes.oneOfType([
      PropTypes.bool,
      PropTypes.number,
      PropTypes.string,
      PropTypes.array,
      PropTypes.object,
    ]),
    dataMappingType: PropTypes.string.isRequired,
    mappingExpression: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).isRequired,
    jsonLogicExpression: PropTypes.object,
    jqExpression: PropTypes.string,
  }),
};

export default ServiceFetchConfigurationPicker;

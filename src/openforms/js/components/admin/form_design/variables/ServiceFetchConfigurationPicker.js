import {useFormik} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

import {FormLogicContext} from './../Context';
import ServiceFetchConfigurationForm from './ServiceFetchConfigurationForm';

const ServiceFetchConfigurationPicker = ({onChange, onFormSave}) => {
  const formLogicContext = useContext(FormLogicContext);

  const [selectExisting, setSelectExisting] = useState(false);
  const [selectedServiceFetchConfig, setSelectedServiceFetchConfig] = useState(null);

  const serviceFetchConfigurationChoices = formLogicContext.serviceFetchConfigurations.map(
    fetchConfig => {
      return [
        fetchConfig.url,
        fetchConfig.name || `${fetchConfig.method} ${fetchConfig.path} (${fetchConfig.service})`,
      ];
    }
  );

  const formik = useFormik({
    initialValues: {
      method: 'GET',
      service: '',
      path: '',
      queryParams: [['', ['']]],
      headers: [['', '']],
      body: '',
      dataMappingType: '',
      mappingExpression: '',
      // These fields are mapped to mappingExpression on save
      jsonLogicExpression: '',
      jqExpression: '',
    },
    onSubmit: (values, {setSubmitting}) => {
      switch (values.dataMappingType) {
        case 'JsonLogic':
          values.mappingExpression = values.jsonLogicExpression;
          break;
        case 'jq':
          values.mappingExpression = values.jqExpression;
          break;
      }
      delete values.jsonLogicExpression;
      delete values.jqExpression;

      alert(JSON.stringify(values, null, 2));
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
                formik.setValues(
                  formLogicContext.serviceFetchConfigurations.find(
                    element => element.url === event.target.value
                  ) || formik.initialValues
                );

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
  onChange: PropTypes.func.isRequired,
  onFormSave: PropTypes.func.isRequired,
};

export default ServiceFetchConfigurationPicker;

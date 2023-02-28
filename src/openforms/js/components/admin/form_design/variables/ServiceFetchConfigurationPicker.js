import {useFormik} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

import {FormLogicContext} from './../Context';
import ServiceFetchConfigurationForm from './ServiceFetchConfigurationForm';

const ServiceFetchConfigurationPicker = ({data = {}, onChange, onFormSave}) => {
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
    },
    onSubmit: (values, {setSubmitting}) => {
      alert(JSON.stringify(values, null, 2));
    },
  });

  return (
    <div className="servicefetchconfiguration-picker">
      <div className="servicefetchconfiguration-select">
        <FormRow>
          <Field
            name={'fetchConfiguration.existing'}
            label={
              <FormattedMessage
                defaultMessage="Choose existing configuration"
                description="Service fetch configuration modal select existing field label"
              />
            }
          >
            <Select
              name="fetchConfiguration.existing"
              choices={serviceFetchConfigurationChoices}
              value={selectedServiceFetchConfig}
              onChange={event => {
                onChange(event);
                setSelectedServiceFetchConfig(event.target.value);
                formik.setValues(
                  formLogicContext.serviceFetchConfigurations.find(
                    element => element.url === event.target.value
                  )
                );

                setSelectExisting(!!event.target.value);
              }}
              allowBlank
            />
          </Field>
        </FormRow>
      </div>

      <div className="servicefetchconfiguration-form">
        <ServiceFetchConfigurationForm
          formik={formik}
          selectExisting={selectExisting}
          onFormSave={onFormSave}
          onChange={onChange}
        />
      </div>
    </div>
  );
};

ServiceFetchConfigurationPicker.propTypes = {
  onReplace: PropTypes.func.isRequired,
};

export default ServiceFetchConfigurationPicker;

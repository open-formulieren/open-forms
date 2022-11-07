import React from 'react';
import PropTypes from 'prop-types';

import {TextInput, NumberInput, DateTimeInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import ArrayInput from 'components/admin/forms/ArrayInput';
import JsonWidget from 'components/admin/forms/JsonWidget';

import {BOOL_OPTIONS} from './constants';

const CheckboxChoices = ({name, value, onChange}) => {
  return (
    <Select
      name={name}
      choices={BOOL_OPTIONS}
      allowBlank
      onChange={onChange}
      value={value}
      translateChoices={true}
    />
  );
};

CheckboxChoices.propTypes = {
  name: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]), // String for empty value
  onChange: PropTypes.func,
};

const WrapperArrayInput = ({name, value, onChange}) => {
  return (
    <ArrayInput
      name={name}
      values={value}
      onChange={value => {
        const fakeEvent = {target: {name: name, value: value}};
        onChange(fakeEvent);
      }}
      inputType="text"
    />
  );
};

WrapperArrayInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.arrayOf(PropTypes.string),
  onChange: PropTypes.func,
};

const WrappedJsonWidget = ({name, value, onChange}) => {
  return <JsonWidget name={name} logic={value} onChange={onChange} cols={25} />;
};

WrappedJsonWidget.propTypes = {
  name: PropTypes.string,
  value: PropTypes.object,
  onChange: PropTypes.func,
};

const WrappedDatetimeInput = ({name, value, onChange}) => {
  const formatDatetime = selectedDatetime => {
    // selectedDatetime is a JS Date where the time is 00:00. When converting to a ISOString, the timezone difference
    // is removed from the time to convert it to a UTC+00 time (which can change the date). So we set the time so that
    // when it is converted to UTC+00 it remains the same day.
    const timezoneOffset = -selectedDatetime.getTimezoneOffset() / 60;
    selectedDatetime.setHours(selectedDatetime.getHours() + timezoneOffset);
    return selectedDatetime;
  };

  return (
    <DateTimeInput
      name={name}
      value={value}
      formatDatetime={formatDatetime}
      onChange={onChange}
      defaultDate={value || null}
    />
  );
};

WrappedDatetimeInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.object,
  onChange: PropTypes.func,
};

const TYPE_TO_INPUT_TYPE = {
  float: NumberInput,
  string: TextInput,
  datetime: WrappedDatetimeInput,
  boolean: CheckboxChoices,
  array: WrapperArrayInput,
  object: WrappedJsonWidget,
  int: NumberInput,
};

const LiteralValueInput = ({name, type, value, onChange, ...extraProps}) => {
  const InputComponent = TYPE_TO_INPUT_TYPE[type] || TextInput;

  const onInputChange = event => {
    const inputValue = event.target.value;
    let value;

    // do any input type conversions if needed, e.g. date to native datetime/ISO-8601 format
    switch (type) {
      case 'float': {
        value = Number.parseFloat(inputValue);
        break;
      }
      case 'int': {
        value = Number.parseInt(inputValue);
        break;
      }
      default:
        value = inputValue;
    }

    onChange({
      target: {
        name: event.target.name,
        value: value,
      },
    });
  };

  if (value === null || value === undefined) value = '';

  return <InputComponent name={name} value={value} onChange={onInputChange} {...extraProps} />;
};

LiteralValueInput.propTypes = {
  name: PropTypes.string.isRequired,
  type: PropTypes.string,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
    PropTypes.array,
    PropTypes.object,
  ]),
  onChange: PropTypes.func.isRequired,
};

export default LiteralValueInput;

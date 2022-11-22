import React, {useContext, useEffect, useRef} from 'react';
import PropTypes from 'prop-types';
import flatpickr from 'flatpickr';

import {PrefixContext} from './Context';

const Input = ({type = 'text', name, ...extraProps}) => {
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  return <input type={type} name={name} {...extraProps} />;
};

Input.propTypes = {
  type: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
};

const TextInput = ({noVTextField, ...props}) => (
  <Input type="text" className={noVTextField ? '' : 'vTextField'} {...props} />
);

const TextArea = ({name, rows = 5, cols = 10, ...extraProps}) => {
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  return <textarea name={name} rows={rows} cols={cols} {...extraProps} />;
};

const NumberInput = props => <Input type="number" {...props} />;

const DateInput = props => <Input type="date" {...props} />;

const DateTimeInput = ({name, value, formatDatetime, onChange, ...extraProps}) => {
  const datetimePickerRef = useRef();

  const wrappedOnChange = (selectedDates, dateStr, instance) => {
    let selectedDatetime = selectedDates[0];
    if (formatDatetime) selectedDatetime = formatDatetime(selectedDatetime);

    const fakeEvent = {
      target: {name: name, value: selectedDatetime.toISOString()},
    };
    onChange(fakeEvent);
  };

  useEffect(() => {
    flatpickr(datetimePickerRef.current, {
      onChange: wrappedOnChange,
      ...extraProps,
    });
  }, []);

  return (
    <div className="datetime-input">
      <input ref={datetimePickerRef} />
    </div>
  );
};

DateTimeInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.string,
  formatDatetime: PropTypes.func,
  onChange: PropTypes.func,
};

const Checkbox = ({name, label, helpText, ...extraProps}) => {
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  const idFor = `id_${name}`;
  return (
    <div className="checkbox-row">
      <input type="checkbox" name={name} id={idFor} {...extraProps} />
      <label className="vCheckboxLabel inline" htmlFor={idFor}>
        {label}
      </label>
      {helpText ? <div className="help">{helpText}</div> : null}
    </div>
  );
};

Checkbox.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  helpText: PropTypes.node,
};

const Radio = ({name, idFor, label, helpText, ...extraProps}) => {
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  idFor = idFor ? idFor : `id_${name}`;
  extraProps.id = idFor; // Override possibly propagated id
  return (
    <label htmlFor={idFor}>
      <input type="radio" name={name} className="radiolist" {...extraProps} />
      {label}
    </label>
  );
};

Radio.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  helpText: PropTypes.node,
};

export {Input, TextInput, TextArea, NumberInput, DateInput, DateTimeInput, Checkbox, Radio};

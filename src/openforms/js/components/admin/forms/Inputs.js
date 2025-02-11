import classNames from 'classnames';
import flatpickr from 'flatpickr';
import PropTypes from 'prop-types';
import React, {useContext, useEffect, useRef} from 'react';
import {defineMessage, useIntl} from 'react-intl';

import {FAIcon} from 'components/admin/icons';

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
  const intl = useIntl();

  const wrappedOnChange = (selectedDates, dateStr, instance) => {
    let formattedDatetime = dateStr;
    if (formatDatetime) formattedDatetime = formatDatetime(selectedDates[0]);

    const fakeEvent = {
      target: {name: name, value: formattedDatetime},
    };
    onChange(fakeEvent);
  };

  useEffect(() => {
    const flatpickrInstance = flatpickr(datetimePickerRef.current, {
      onChange: wrappedOnChange,
      ...extraProps,
    });

    return function cleanup() {
      flatpickrInstance.destroy();
    };
  }, []);

  const placeHolder =
    extraProps.placeholder ??
    intl.formatMessage(
      defineMessage({
        description: 'datetime input widget placeholder',
        defaultMessage: 'Select date/time...',
      })
    );

  return (
    <div className="datetime-input">
      <input
        ref={datetimePickerRef}
        placeholder={placeHolder}
        value={value ?? ''}
        onChange={onChange}
      />
      <FAIcon
        title={intl.formatMessage({
          description: 'Delete datetime value',
          defaultMessage: 'Remove value',
        })}
        icon="times"
        onClick={() => {
          onChange({target: {name, value: ''}});
        }}
      />
    </div>
  );
};

DateTimeInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.string,
  formatDatetime: PropTypes.func,
  onChange: PropTypes.func,
};

const Checkbox = ({
  name,
  label,
  helpText,
  noVCheckbox = false,
  fullWidth = false,
  ...extraProps
}) => {
  const {disabled = false} = extraProps;
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  const idFor = disabled ? undefined : `id_${name}`;
  return (
    <div className={classNames({'field--disabled': disabled, 'w-100': fullWidth})}>
      <div className="flex-container checkbox-row">
        <input type="checkbox" name={name} id={idFor} {...extraProps} />{' '}
        <label className={classNames('inline', {vCheckboxLabel: !noVCheckbox})} htmlFor={idFor}>
          {label}
        </label>
      </div>
      {helpText && (
        <div className="help">
          <div>{helpText}</div>
        </div>
      )}
    </div>
  );
};

Checkbox.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  helpText: PropTypes.node,
  noVCheckbox: PropTypes.bool,
  fullWidth: PropTypes.bool,
};

const Radio = ({name, idFor, label, helpText, ...extraProps}) => {
  const {disabled = false} = extraProps;
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  idFor = idFor ? idFor : `id_${name}`;
  if (disabled) {
    idFor = undefined;
  }
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

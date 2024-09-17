import {getReactSelectStyles} from '@open-formulieren/formio-builder/esm/components/formio/select';
import classNames from 'classnames';
import {useField} from 'formik';
import PropTypes from 'prop-types';
import ReactSelect from 'react-select';

const initialStyles = getReactSelectStyles();
const styles = {
  ...initialStyles,
  control: (...args) => ({
    ...initialStyles.control(...args),
    minHeight: '1.875rem',
    height: '1.875rem',
  }),
  valueContainer: (...args) => ({
    ...initialStyles.valueContainer(...args),
    height: 'calc(1.875rem - 2px)',
    padding: '0 6px',
  }),
  input: (...args) => ({
    ...initialStyles.input(...args),
    margin: '0px',
  }),
  indicatorsContainer: baseStyles => ({
    ...baseStyles,
    height: 'calc(1.875rem - 2px)',
    padding: '0 2px',
  }),
  dropdownIndicator: (...args) => ({
    ...initialStyles.dropdownIndicator(...args),
    padding: '5px 2px',
  }),
};

const getValueRecursively = (options, value) => {
  if (!value) {
    return null;
  }

  const option = options.find(opt => opt.value === value);
  if (option) {
    return option;
  }

  // Search for the option recursively
  for (let i = 0; i < options.length; i++) {
    const opt = options[i];
    if (!opt.options) {
      continue;
    }

    const option = getValueRecursively(opt.options, value);
    if (option) {
      return option;
    }
  }

  return null;
};

/**
 * A select dropdown backed by react-select for legacy usage.
 *
 * Any additional props are forwarded to the underlying ReactSelect component.
 *
 * @deprecated - if possible, refactor the form to use Formik and use the Formik-enabled
 * variant.
 */
const SelectWithoutFormik = ({name, options, value, className, onChange, ...props}) => {
  const classes = classNames('admin-react-select', {
    [`${className}`]: className,
  });
  return (
    <ReactSelect
      inputId={`id_${name}`}
      name={name}
      className={classes}
      classNamePrefix="admin-react-select"
      styles={styles}
      menuPlacement="auto"
      options={options}
      value={getValueRecursively(options, value)}
      onChange={selectedOption => {
        onChange(selectedOption === null ? undefined : selectedOption.value);
      }}
      {...props}
    />
  );
};

/**
 * A select dropdown backed by react-select for Formik forms.
 *
 * Any additional props are forwarded to the underlying ReactSelect component.
 */
const SelectWithFormik = ({name, options, className, ...props}) => {
  const [fieldProps, , fieldHelpers] = useField(name);
  const {value} = fieldProps;
  const {setValue} = fieldHelpers;
  const classes = classNames('admin-react-select', {
    [`${className}`]: className,
  });
  return (
    <ReactSelect
      inputId={`id_${name}`}
      className={classes}
      classNamePrefix="admin-react-select"
      styles={styles}
      menuPlacement="auto"
      options={options}
      {...fieldProps}
      value={getValueRecursively(options, value)}
      onChange={selectedOption => {
        // clear the value
        if (selectedOption == null) {
          setValue(undefined);
        } else {
          setValue(selectedOption.value);
        }
      }}
      {...props}
    />
  );
};

SelectWithoutFormik.propTypes = {
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  options: PropTypes.arrayOf(PropTypes.object),
};

SelectWithFormik.propTypes = {
  name: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(PropTypes.object),
};

export default SelectWithFormik;
export {SelectWithFormik, SelectWithoutFormik};

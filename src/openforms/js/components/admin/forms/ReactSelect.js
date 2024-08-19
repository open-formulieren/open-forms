import {getReactSelectStyles} from '@open-formulieren/formio-builder/esm/components/formio/select';
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

/**
 * A select dropdown backed by react-select for Formik forms.
 *
 * Any additional props are forwarded to the underlyng ReactSelect component.
 */
const Select = ({name, options, ...props}) => {
  const [fieldProps, , fieldHelpers] = useField(name);
  const {value} = fieldProps;
  const {setValue} = fieldHelpers;
  return (
    <ReactSelect
      inputId={`id_${name}`}
      className="admin-react-select"
      classNamePrefix="admin-react-select"
      styles={styles}
      menuPlacement="auto"
      options={options}
      {...fieldProps}
      value={options.find(opt => opt.value === value) || null}
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

Select.propTypes = {
  name: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(PropTypes.object),
};

export default Select;

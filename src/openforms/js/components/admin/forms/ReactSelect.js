// Inspired/copied from the React Select component in the form builder.
import PropTypes from 'prop-types';
import React from 'react';
import {default as ReactSelectInner} from 'react-select';

// See https://github.com/JedWatson/react-select/blob/master/packages/react-select/src/theme.ts
const BUILDER_SELECT_THEME = theme => ({
  ...theme,
  borderRadius: 4, // same as bootstrap inputs
});

function isOption(opt) {
  return opt.options === undefined;
}

function isOptionGroup(opt) {
  return opt.options !== undefined;
}

function extractSelectedValue(options, currentValue, valueProperty = 'value') {
  const valueTest = opt => currentValue === opt[valueProperty];

  for (const optionOrGroup of options) {
    if (isOption(optionOrGroup) && valueTest(optionOrGroup)) {
      return optionOrGroup;
    }
    if (isOptionGroup(optionOrGroup)) {
      for (const option of optionOrGroup.options) {
        if (valueTest(option)) {
          return option;
        }
      }
    }
  }
}

const ReactSelect = ({
  name,
  value,
  options,
  onChange,
  htmlId,
  isClearable = true,
  valueProperty = 'value',
  emptyValue = null,
}) => {
  const valueOption = extractSelectedValue(options, value, valueProperty) ?? '';

  return (
    <ReactSelectInner
      value={valueOption}
      onChange={(newValue, action) => {
        const rawValue = newValue?.[valueProperty] ?? emptyValue;
        onChange({target: {name, value: rawValue}});
      }}
      inputId={htmlId}
      options={options}
      isClearable={isClearable}
      menuPlacement="auto"
      theme={BUILDER_SELECT_THEME}
      styles={{
        control: (baseStyles, state) => ({
          ...baseStyles,
          backgroundColor: 'var(--form-input-bg, #fff)',
          borderColor: state.isFocused
            ? 'var(--body-quiet-color, #666)'
            : 'var(--border-color, #ccc)',
          boxShadow: undefined,
          '&:hover': {
            borderColor: undefined,
          },
        }),
        placeholder: baseStyles => ({
          ...baseStyles,
          color: 'var(--body-quiet-color, #e0e0e0)',
        }),
        indicatorSeparator: baseStyles => ({
          ...baseStyles,
          backgroundColor: 'var(--border-color, #ccc)',
        }),
        dropdownIndicator: baseStyles => ({
          ...baseStyles,
          color: 'var(--body-quiet-color, #e0e0e0)',
          '&:hover': {
            color: 'var(--body-loud-color, #000)',
          },
        }),
        clearIndicator: baseStyles => ({
          ...baseStyles,
          color: 'var(--body-quiet-color, #e0e0e0)',
          '&:hover': {
            color: 'var(--body-loud-color, #000)',
          },
        }),
        valueContainer: baseStyles => ({
          ...baseStyles,
          color: 'var(--body-fg, #333)',
        }),
        input: baseStyles => ({
          ...baseStyles,
          color: 'var(--body-fg, #333)',
        }),
        singleValue: baseStyles => ({
          ...baseStyles,
          color: 'var(--body-fg, #333)',
        }),
        multiValue: baseStyles => ({
          ...baseStyles,
          backgroundColor: 'var(--default-button-bg, #017092)',
        }),
        multiValueLabel: baseStyles => ({
          ...baseStyles,
          color: 'var(--formio-dropdown-value-label-color, #fff)',
        }),
        multiValueRemove: baseStyles => ({
          ...baseStyles,
          color: 'var(--formio-dropdown-value-label-color, #fff)',
        }),
        menu: baseStyles => ({
          ...baseStyles,
          backgroundColor: 'var(--form-input-bg, #fff)',
          borderColor: 'var(--border-color, #ccc)',
        }),
        menuList: baseStyles => ({
          ...baseStyles,
          border: 'solid 1px var(--border-color, #ccc)',
          borderRadius: '4px',
        }),
        option: (baseStyles, state) => ({
          ...baseStyles,
          color: 'var(--body-fg, #333)',
          backgroundColor: state.isFocused
            ? 'var(--formio-dropdown-highlighted-bg, #f2f2f2)'
            : undefined,
        }),
      }}
    />
  );
};

ReactSelect.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  isClearable: PropTypes.bool,
  valueProperty: PropTypes.string,
  emptyValue: PropTypes.any,
};

export default ReactSelect;

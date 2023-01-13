import cloneDeep from 'lodash/cloneDeep';

import jsonScriptToVar from 'utils/json-script';

const getCustomValidationErrorMessagesEditForm = validators => {
  const defaultValues = Object.assign(
    {},
    ...validators.map(validator => ({
      [validator.key.split('.')[1]]: '',
    }))
  );

  const languages = jsonScriptToVar('languages', {default: []});

  const customErrorMessages = languages.map(([languageCode, _label]) => {
    return {
      key: languageCode,
      label: languageCode.toUpperCase(),
      components: [
        {
          type: 'datamap',
          input: true,
          key: `translatedErrors.${languageCode}`,
          tooltip: 'Custom errors and their translation.',
          keyLabel: 'Error',
          disableKey: true,
          disableAddingRemovingRows: true,
          hideLabel: true,
          reorder: false,
          defaultValue: defaultValues,
          valueComponent: {
            type: 'textfield',
            key: 'message',
            label: 'Message',
            input: true,
            hideLabel: true,
            tableView: true,
          },
        },
      ],
    };
  });

  return {
    type: 'panel',
    legend: 'Custom error messages',
    title: 'Custom error messages',
    key: 'translatedErrors',
    tooltip: 'Custom error messages for this component and their translations',
    collapsible: true,
    collapsed: true,
    components: [
      {
        key: 'translations',
        components: [
          {
            key: 'languages',
            type: 'tabs',
            components: customErrorMessages,
          },
        ],
      },
    ],
  };
};

const getValidationEditForm = validationEditForm => {
  let updatedEditForm = cloneDeep(validationEditForm);
  updatedEditForm.components = updatedEditForm.components.filter(
    component => component.key !== 'translatedErrors'
  );

  const customErrorComponent = getCustomValidationErrorMessagesEditForm(
    // TODO The plugins validators have error messages hardcoded in the backend. Ignoring them for now
    updatedEditForm.components.filter(component => component.key !== 'validate.plugins')
  );
  updatedEditForm.components.push(customErrorComponent);

  return updatedEditForm;
};

export {getValidationEditForm};

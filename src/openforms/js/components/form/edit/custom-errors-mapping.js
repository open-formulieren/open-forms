import jsonScriptToVar from 'utils/json-script';

const customErrorMapping = {
  default: ['required'],
  textfield: ['required', 'maxLength', 'pattern'],
};

const LANGUAGES = jsonScriptToVar('languages', {default: []});

const getCustomValidationErrorMessagesEditForm = componentType => {
  const defaultValues = Object.assign(
    {},
    ...(customErrorMapping[componentType] || customErrorMapping.default).map(errorKey => ({
      [errorKey]: '',
    }))
  );
  const customErrorMessages = LANGUAGES.map(([languageCode, _label]) => {
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
            components: getCustomValidationErrorMessagesEditForm,
          },
        ],
      },
    ],
  };
};

export {customErrorMapping};

import cloneDeep from 'lodash/cloneDeep';

import {getSupportedLanguages} from 'components/formio_builder/translation';

const getCustomValidationErrorMessagesEditForm = validators => {
  const defaultValues = Object.assign(
    {},
    ...validators.map(validator => ({
      [validator.key.split('.')[1]]: '',
    }))
  );

  const languages = getSupportedLanguages();

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
        type: 'htmlelement',
        tag: 'div',
        // Work around to avoid {{ field }} being parsed by Formio.
        // Taken from https://github.com/formio/formio.js/blob/v4.14.12/src/components/_classes/component/editForm/Component.edit.validation.js#L165
        content: `
        <div>
          Below you can set different error messages for different errors. You can reference the label of the field
          with the expression <code>{<span />{ field }}</code>.
          <br />
          For example, for a required field the error can be: "{<span/>{ field }} is required. Try again."
        </div>`,
      },
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

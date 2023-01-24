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
        </div>

        <pre>{
          "required": "{<span/>{ field }} is required. Try again.",
          "maxLength": "{<span/>{ field }} is too long. Try again."
        }</pre>
          <p>You can set the following keys (among others):</p>
          <ul>
            <li>r<span/>equired</li>
            <li>m<span/>in</li>
            <li>m<span/>ax</li>
            <li>m<span/>inLength</li>
            <li>m<span/>axLength</li>
            <li>m<span/>inWords</li>
            <li>m<span/>axWords</li>
            <li>i<span/>nvalid_email</li>
            <li>i<span/>nvalid_date</li>
            <li>i<span/>nvalid_day</li>
            <li>i<span/>nvalid_regex</li>
            <li>m<span/>ask</li>
            <li>p<span/>attern</li>
            <li>c<span/>ustom</li>
          </ul>

          <p>Depending on the error message some of the following template variables can be used in the script:</p>
          <ul>
           <li><code>{<span/>{ f<span/>ield }}</code> is replaced with the label of the field.</li>
           <li><code>{<span/>{ m<span/>in }}</code></li>
           <li><code>{<span/>{ m<span/>ax }}</code></li>
           <li><code>{<span/>{ l<span/>ength }}</code></li>
           <li><code>{<span/>{ p<span/>attern }}</code></li>
           <li><code>{<span/>{ m<span/>inDate }}</code></li>
           <li><code>{<span/>{ m<span/>axDate }}</code></li>
           <li><code>{<span/>{ m<span/>inYear }}</code></li>
           <li><code>{<span/>{ m<span/>axYear }}</code></li>
           <li><code>{<span/>{ r<span/>egex }}</code></li>
          </ul>
          `,
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

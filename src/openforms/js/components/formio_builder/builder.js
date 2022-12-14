import cloneDeep from 'lodash/cloneDeep';
import React, {useRef, useEffect, useState, useContext} from 'react';
import PropTypes from 'prop-types';
import {FormBuilder, Templates} from 'react-formio';
import {FormStepContext} from '../admin/form_design/Context';

import jsonScriptToVar from '../../utils/json-script';
import nlStrings from './translation';
import customTemplates from './customTemplates';

Templates.current = customTemplates;

const TRANSLATABLE_FIELDS = [
  'label',
  'description',
  'placeholder',
  'defaultValue',
  'tooltip',
  'values.label',
];

const getValuesOfField = (component, fieldName) => {
  let values = [];
  if (fieldName.includes('.')) {
    const [prefix, inner] = fieldName.split('.');
    for (const entry of component[prefix] || []) {
      values.push(entry[inner]);
    }
  } else {
    let value = component[fieldName];
    if (!value) return [];
    else if (typeof value === 'object' && !Array.isArray(value)) return [];

    values.push(component[fieldName]);
  }
  return values;
};

const injectTranslationsIntoConfiguration = (configuration, componentTranslations) => {
  let translationMapping = {};

  if (configuration.components) {
    configuration.components.forEach(component => {
      injectTranslationsIntoConfiguration(component, componentTranslations);
    });
  }

  if (configuration.display !== 'form') {
    let values = [];
    for (const field of TRANSLATABLE_FIELDS) {
      values = values.concat(getValuesOfField(configuration, field));
    }

    let mutatedTranslations = {};
    for (const [languageCode, translations] of Object.entries(componentTranslations)) {
      for (const [literal, translation] of Object.entries(translations)) {
        if (values.includes(literal)) {
          mutatedTranslations[languageCode] = (mutatedTranslations[languageCode] || []).concat([
            {literal: literal, translation: translation},
          ]);
        }
      }
    }
    configuration['of-translations'] = mutatedTranslations;
  }
};

const getBuilderOptions = () => {
  const maxFileUploadSize = jsonScriptToVar('setting-MAX_FILE_UPLOAD_SIZE');
  const formFieldsRequiredDefault = jsonScriptToVar('config-REQUIRED_DEFAULT');

  return {
    builder: {
      basic: false,
      advanced: false,
      data: false,
      layout: false,
      premium: false,

      custom: {
        default: true,
        title: 'Formuliervelden',
        weight: 0,
        components: {
          textfield: true,
          textarea: true,
          checkbox: true,
          selectboxes: true,
          select: true,
          radio: true,
          number: true,
          currency: true,
          email: true,
          date: true,
          time: true,
          phoneNumber: true,
          postcode: true,
          file: true,
          password: true,
        },
      },
      custom_special: {
        title: 'Special fields',
        weight: 5,
        components: {
          iban: true,
          licenseplate: true,
          bsn: true,
          npFamilyMembers: true,
          signature: true,
          coSign: true,
          map: true,
          editgrid: true,
        },
      },
      custom_layout: {
        title: 'Opmaak',
        weight: 5,
        components: {
          content: true,
          fieldset: true,
          columns: true,
        },
      },
    },
    noDefaultSubmitButton: true,
    language: 'nl',
    i18n: {
      nl: nlStrings,
    },
    evalContext: {
      serverUploadLimit: maxFileUploadSize,
      requiredDefault: formFieldsRequiredDefault,
    },
    editors: {
      ckeditor: {
        settings: {
          toolbar: {
            items: [
              'heading',
              'fontFamily',
              'fontSize',
              'fontColor',
              '|',
              'bold',
              'italic',
              'link',
              'bulletedList',
              'numberedList',
              '|',
              'indent',
              'outdent',
              '|',
              'imageUpload',
              'blockQuote',
              'insertTable',
              'mediaEmbed',
              'alignment:left',
              'alignment:right',
              'alignment:center',
              'undo',
              'redo',
            ],
          },
          link: {
            decorators: {
              openInNewTab: {
                mode: 'manual',
                label: 'Open in a new tab',
                defaultValue: true, // This option will be selected by default.
                attributes: {
                  target: '_blank',
                  rel: 'noopener noreferrer',
                },
              },
            },
          },
          fontColor: {
            colors: jsonScriptToVar('config-RICH_TEXT_COLORS'),
          },
        },
      },
    },
  };
};

const FormIOBuilder = ({configuration, onChange, onComponentMutated, forceUpdate = false}) => {
  // the deep clone is needed to create a mutable object, as the FormBuilder
  // mutates this object when forms are edited.
  const clone = cloneDeep(configuration);
  // using a ref that is never updated allows us to create a mutable object _once_
  // and hold that reference and pass it down to the builder. Because the reference
  // never changes, the prop never changes, and re-renders of the form builder are
  // avoided. This prevents an infinite loop, reported here: https://github.com/formio/react/issues/386
  // The onChange events fires for every render. So, if the onChange event causes props
  // to change (by reference, not by value!), you end up in an infite loop.
  //
  // This approach effectively pins the FormBuilder.form prop reference.
  const formRef = useRef(clone);
  const {componentTranslations} = useContext(FormStepContext);

  // TODO instead of injecting this into the configuration, the componentTranslations
  // should be passed to the components, and each component should then determine which
  // translations are relevant. Additionally, there should be an onChange event that
  // mutates these componentTranslations when changing labels/translations, such that
  // the displayed translations are always up to date
  injectTranslationsIntoConfiguration(clone, componentTranslations);

  // track some state to force re-renders, and we can also keep track of the amount of
  // re-renders that way for debugging purposes.
  const [rerenders, setRerenders] = useState(0);

  // props need to be immutable to not end up in infinite loops
  const [builderOptions] = useState(getBuilderOptions());

  // if an update must be forced, we mutate the ref state to point to the new
  // configuration, which causes the form builder to re-render the new configuration.
  useEffect(() => {
    if (forceUpdate) {
      formRef.current = clone;
      setRerenders(rerenders + 1);
    }
  });

  const extraProps = {};

  if (onComponentMutated) {
    extraProps.onSaveComponent = onComponentMutated.bind(null, 'changed');
    extraProps.onDeleteComponent = onComponentMutated.bind(null, 'removed');
  }

  return (
    <FormBuilder
      form={formRef.current}
      options={builderOptions}
      onChange={formSchema => onChange(cloneDeep(formSchema))}
      {...extraProps}
    />
  );
};

FormIOBuilder.propTypes = {
  configuration: PropTypes.object,
  onChange: PropTypes.func,
  onComponentMutated: PropTypes.func,
  forceUpdate: PropTypes.bool,
};

export default FormIOBuilder;

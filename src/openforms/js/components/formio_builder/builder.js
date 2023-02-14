import cloneDeep from 'lodash/cloneDeep';
import isEqual from 'lodash/isEqual';
import set from 'lodash/set';
import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {FormBuilder, Templates} from 'react-formio';

import jsonScriptToVar from 'utils/json-script';

import customTemplates from './customTemplates';
import nlStrings, {
  addTranslationForLiteral,
  handleComponentValueLiterals,
  isTranslatableProperty,
} from './translation';

Templates.current = customTemplates;

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
          datetime: true,
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
      custom_preset: {
        title: 'Voorgedefinieerd',
        weight: 10,
        components: {
          fullName: {
            title: 'Volledige naam',
            key: 'fullName',
            icon: 'terminal',
            schema: {
              label: 'Volledige naam',
              autocomplete: 'off',
              type: 'textfield',
              key: 'fullName',
              input: true,
            },
          },
          firstName: {
            title: 'Voornaam',
            key: 'firstName',
            icon: 'terminal',
            schema: {
              label: 'Voornaam',
              autocomplete: 'off',
              type: 'textfield',
              key: 'firstName',
              input: true,
            },
          },
          lastName: {
            title: 'Achternaam',
            key: 'lastName',
            icon: 'terminal',
            schema: {
              label: 'Achternaam',
              autocomplete: 'off',
              type: 'textfield',
              key: 'lastName',
              input: true,
            },
          },
          addressLine1: {
            title: 'Adresregel 1',
            key: 'addressLine1',
            icon: 'home',
            schema: {
              label: 'Adresregel 1',
              autocomplete: 'address-line1',
              type: 'textfield',
              key: 'addressLine1',
              input: true,
            },
          },
          addressLine2: {
            title: 'Adresregel 2',
            key: 'addressLine2',
            icon: 'home',
            schema: {
              label: 'Adresregel 2',
              autocomplete: 'address-line2',
              type: 'textfield',
              key: 'addressLine2',
              input: true,
            },
          },
          addressLine3: {
            title: 'Adresregel 3',
            key: 'addressLine3',
            icon: 'home',
            schema: {
              label: 'Adresregel 3',
              autocomplete: 'address-line3',
              type: 'textfield',
              key: 'addressLine3',
              input: true,
            },
          },
          postalcode: {
            title: 'Postcode',
            key: 'postalcode',
            icon: 'home',
            schema: {
              label: 'Postcode',
              autocomplete: 'postal-code',
              type: 'textfield',
              key: 'postalcode',
              input: true,
              inputMask: '9999 AA',
              validateOn: 'blur',
              validate: {
                customMessage: 'Invalid Postcode',
                // Dutch postcode has 4 numbers and 2 letters (case insensitive). Letter combinations SS, SD and SA
                // are not used due to the Nazi-association.
                // See https://stackoverflow.com/a/17898538/7146757 and https://nl.wikipedia.org/wiki/Postcodes_in_Nederland
                pattern: '^[1-9][0-9]{3} ?(?!sa|sd|ss|SA|SD|SS)[a-zA-Z]{2}$',
              },
            },
          },
          email: {
            title: 'E-mailadres',
            key: 'email',
            icon: 'at',
            schema: {
              label: 'E-mailadres',
              autocomplete: 'email',
              tableView: true,
              key: 'email',
              type: 'email',
              input: true,
            },
          },
          phoneNumber: {
            title: 'Telefoonnummer',
            key: 'phoneNumber',
            icon: 'phone-square',
            schema: {
              label: 'Telefoonnummer',
              autocomplete: 'tel',
              tableView: true,
              key: 'phoneNumber',
              type: 'phoneNumber',
              input: true,
            },
          },
          password: {
            title: 'Huidig wachtwoord',
            key: 'password',
            icon: 'asterisk',
            schema: {
              label: 'Huidig wachtwoord',
              autocomplete: 'current-password',
              tableView: true,
              key: 'password',
              type: 'password',
              input: true,
            },
          },
          newPassword: {
            title: 'Nieuw wachtwoord',
            key: 'newPassword',
            icon: 'asterisk',
            schema: {
              label: 'Nieuw wachtwoord',
              autocomplete: 'new-password',
              tableView: true,
              key: 'newPassword',
              type: 'password',
              input: true,
            },
          },
          url: {
            title: 'Website',
            key: 'url',
            icon: 'link',
            schema: {
              label: 'Website',
              autocomplete: 'url',
              type: 'textfield',
              key: 'url',
              input: true,
            },
          },
        },
      },
      custom_deprecated: {
        title: 'Verouderd',
        weight: 15,
        components: {
          postcode: true,
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

const FormIOBuilder = ({
  configuration,
  onChange,
  onComponentMutated,
  componentTranslations = {}, // mapping of language code to (mapping of literal -> translation)
  forceUpdate = false,
}) => {
  // the deep clone is needed to create a mutable object, as the FormBuilder
  // mutates this object when forms are edited.
  const clone = cloneDeep(configuration);
  // using a ref that is never updated allows us to create a mutable object _once_
  // and hold that reference and pass it down to the builder. Because the reference
  // never changes, the prop never changes, and re-renders of the form builder are
  // avoided. This prevents an infinite loop, reported here: https://github.com/formio/react/issues/386
  // The onChange events fires for every render. So, if the onChange event causes props
  // to change (by reference, not by value!), you end up in an infinite loop.
  //
  // This approach effectively pins the FormBuilder.form prop reference.
  const formRef = useRef(clone);
  const previousLiteralsRef = useRef({});

  const componentTranslationsRef = useRef(componentTranslations);

  // ... The onChange event of the builder is only bound once, so while the
  // onBuilderFormChange function identity changes with every render, the formio builder
  // instance actually only knows about the very first one. This means our updated state/
  // props that's checked in the callbacks is an outdated view, which we can fix by using
  // mutable refs :-)
  useEffect(() => {
    const localComponentTranslations = componentTranslationsRef.current;
    if (!isEqual(localComponentTranslations, componentTranslations)) {
      componentTranslationsRef.current = componentTranslations;
    }
  });

  // track some state to force re-renders, and we can also keep track of the amount of
  // re-renders that way for debugging purposes.
  const [rerenders, setRerenders] = useState(0);

  // props need to be immutable to not end up in infinite loops
  const [builderOptions] = useState(getBuilderOptions());

  // https://help.form.io/developers/form-renderer#form-events
  const onBuilderFormChange = (changed, flags, modifiedByHuman) => {
    const {instance, value: newLiteral} = flags;

    // Call Formio triggerChange
    instance.root.triggerChange(changed, flags, modifiedByHuman);

    // get the submission data of the form in the modal, which configures the component
    // itself.
    const newComponentConfiguration = instance.root.submission.data;
    // check which translatable properties are relevant
    const changedPropertyPath = instance.path;
    const {type: componentType} = newComponentConfiguration;
    const localComponentTranslations = componentTranslationsRef.current;

    const exposeTranslations = translations => {
      // update the component form submission data, so we have the updated translations
      // in the component.
      instance.root.submission = {
        data: {
          ...newComponentConfiguration,
          openForms: {
            ...(newComponentConfiguration?.openForms || {}),
            translations: translations,
          },
        },
      };
    };

    // the first builder load/iteration sets the values directly by data.values or values,
    // depending on the component type. Subsequent edits of the literals are caught in the
    // normal operation, they show up as data.values[<index>].label and for those the
    // previous literal is properly tracked.
    let newTranslations = handleComponentValueLiterals(
      newComponentConfiguration,
      localComponentTranslations,
      changedPropertyPath,
      newLiteral,
      previousLiteralsRef
    );
    if (newTranslations !== null) {
      exposeTranslations(newTranslations);
      return;
    }

    if (!isTranslatableProperty(componentType, changedPropertyPath)) return;

    // figure out the previous value of the translation literal for this specific
    // component.
    const prevLiteral = previousLiteralsRef.current?.[changedPropertyPath];

    // prevent infinite event loops
    if (newLiteral == prevLiteral) return;

    // update the translations
    newTranslations = addTranslationForLiteral(
      newComponentConfiguration,
      localComponentTranslations,
      prevLiteral,
      newLiteral
    );
    exposeTranslations(newTranslations);
    // update the literal for the next change cycle
    set(previousLiteralsRef.current, [changedPropertyPath], newLiteral);
  };
  // otherwise builder keeps refreshing/remounting
  builderOptions.onChange = onBuilderFormChange;

  const resetEditFormRefs = () => {
    previousLiteralsRef.current = {};
  };

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
    extraProps.onSaveComponent = (...args) => {
      resetEditFormRefs();
      onComponentMutated('changed', ...args);
    };
    extraProps.onDeleteComponent = (...args) => {
      resetEditFormRefs();
      onComponentMutated('removed', ...args);
    };
  }

  return (
    <FormBuilder
      form={formRef.current}
      options={builderOptions}
      onChange={formSchema => onChange(cloneDeep(formSchema))}
      onUpdateComponent={() => (previousLiteralsRef.current = {})}
      onCancelComponent={resetEditFormRefs}
      {...extraProps}
    />
  );
};

FormIOBuilder.propTypes = {
  configuration: PropTypes.object,
  onChange: PropTypes.func,
  onComponentMutated: PropTypes.func,
  componentTranslations: PropTypes.objectOf(PropTypes.objectOf(PropTypes.string)),
  forceUpdate: PropTypes.bool,
};

export default FormIOBuilder;

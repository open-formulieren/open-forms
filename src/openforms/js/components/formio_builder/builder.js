import cloneDeep from 'lodash/cloneDeep';
import set from 'lodash/set';
import PropTypes from 'prop-types';
import React, {useContext, useEffect, useRef, useState} from 'react';
import {FormBuilder, Templates} from 'react-formio';

import {FeatureFlagsContext} from 'components/admin/form_design/Context';
import useOnChanged from 'hooks/useOnChanged';
import jsonScriptToVar from 'utils/json-script';

import customTemplates from './customTemplates';

Templates.current = customTemplates;

const nlStrings = require('lang/formio/nl.json');

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
          cosign: true,
          map: true,
          editgrid: true,
          addressNL: true,
          partners: true,
          children: true,
        },
      },
      custom_layout: {
        title: 'Opmaak',
        weight: 5,
        components: {
          content: true,
          fieldset: true,
          columns: true,
          softRequiredErrors: true,
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
              autocomplete: 'name',
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
              autocomplete: 'given-name',
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
              autocomplete: 'family-name',
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
          coSign: true,
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
  };
};

const FormIOBuilder = ({
  configuration,
  onChange,
  onComponentMutated,
  componentNamespace = {},
  registrationBackendInfo = [],
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

  const componentNamespaceRef = useRef(componentNamespace);
  const registrationBackendInfoRef = useRef(registrationBackendInfo);

  // ... The onChange event of the builder is only bound once, so while the
  // onBuilderFormChange function identity changes with every render, the formio builder
  // instance actually only knows about the very first one. This means our updated state/
  // props that's checked in the callbacks is an outdated view, which we can fix by using
  // mutable refs :-)
  useOnChanged(componentNamespace, () => {
    componentNamespaceRef.current = componentNamespace;
  });

  // track some state to force re-renders, and we can also keep track of the amount of
  // re-renders that way for debugging purposes.
  const [rerenders, setRerenders] = useState(0);

  const featureFlags = useContext(FeatureFlagsContext);

  // props need to be immutable to not end up in infinite loops
  const [builderOptions] = useState(getBuilderOptions());

  set(builderOptions, 'openForms.componentNamespace', componentNamespaceRef.current);
  set(builderOptions, 'openForms.featureFlags', featureFlags);
  set(builderOptions, 'openForms.registrationBackendInfoRef', registrationBackendInfoRef);

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
      onComponentMutated('changed', ...args);
    };
    extraProps.onDeleteComponent = (...args) => {
      onComponentMutated('removed', ...args);
    };
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
  componentNamespace: PropTypes.arrayOf(PropTypes.object),
  forceUpdate: PropTypes.bool,
  registrationBackendInfo: PropTypes.arrayOf(PropTypes.object),
};

export default FormIOBuilder;

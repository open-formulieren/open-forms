import cloneDeep from 'lodash/cloneDeep';
import set from 'lodash/set';
import PropTypes from 'prop-types';
import {useContext, useEffect, useRef, useState} from 'react';
import {FormBuilder, Templates} from 'react-formio';

import {FeatureFlagsContext, FormContext} from 'components/admin/form_design/Context';
import useOnChanged from 'hooks/useOnChanged';
import jsonScriptToVar from 'utils/json-script';

import {BUILDER_FORM_TYPE_MAPPINGS} from './builderData';
import customTemplates from './customTemplates';

Templates.current = customTemplates;

const nlStrings = require('lang/formio/nl.json');

const getBuilderOptions = () => {
  const maxFileUploadSize = jsonScriptToVar('setting-MAX_FILE_UPLOAD_SIZE');
  const formFieldsRequiredDefault = jsonScriptToVar('config-REQUIRED_DEFAULT');
  const formType = jsonScriptToVar('FORM_TYPE');

  return {
    builder: BUILDER_FORM_TYPE_MAPPINGS[formType],
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

  // add custom options here to expose the necessary form context
  const {
    form: {authBackends = []},
    plugins: {availablePrefillPlugins = []},
  } = useContext(FormContext);
  set(builderOptions, 'openForms.authBackends', authBackends);
  set(builderOptions, 'openForms.availablePrefillPlugins', availablePrefillPlugins);

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

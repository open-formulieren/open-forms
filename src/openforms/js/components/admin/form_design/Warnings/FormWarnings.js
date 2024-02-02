import PropTypes from 'prop-types';
import React, {useContext} from 'react';

import {FormContext} from 'components/admin/form_design/Context';
import CosignInRepeatingGroupWarning from 'components/admin/form_design/CosignInRepeatingGroupWarning';
import MissingTranslationsWarning from 'components/admin/form_design/MissingTranslationsWarning';
import MultipleCosignComponentsWarning from 'components/admin/form_design/MultipleCosignComponentsWarning';

import {MissingAuthCosignWarning} from './index';

const FormWarnings = ({form}) => {
  const {formSteps, components} = useContext(FormContext);

  // components is a dictionary where the key is the 'path' of the component. For example, for a component 'foo' in a
  // repeating group 'bar', the key is 'bar.foo'.
  let cosignComponentsWithPath = {};

  const cosignComponentsWithoutPath = Object.entries(components)
    .map(([key, component]) => {
      if (component.type === 'cosign') {
        cosignComponentsWithPath[key] = component;
        return component;
      }
    })
    .filter(Boolean);

  return (
    <>
      {form.translationEnabled ? (
        <MissingTranslationsWarning form={form} formSteps={formSteps} />
      ) : null}
      <MultipleCosignComponentsWarning cosignComponents={cosignComponentsWithoutPath} />
      {cosignComponentsWithoutPath.length === 1 && <MissingAuthCosignWarning />}
      <CosignInRepeatingGroupWarning
        cosignComponents={cosignComponentsWithPath}
        availableComponents={components}
      />
    </>
  );
};

FormWarnings.propTypes = {
  form: PropTypes.object.isRequired,
};

export default FormWarnings;

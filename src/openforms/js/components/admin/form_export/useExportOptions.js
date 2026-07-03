import {useContext} from 'react';

import {FormContext} from 'components/admin/form_design/Context';

/**
 * Get a list of options that should be included in the form configuration. These options
 * represent key parts of the form configuration.
 *
 * The options are based on the form configuration. For example, if the form doesn't have
 * any registration backends, then the registration backends option is not included.
 *
 * @returns {String[]}
 */
export const useFormConfigurationOptions = () => {
  const {registrationBackends, form, formVariables} = useContext(FormContext);
  const {authBackends, paymentBackend} = form;

  const hasRegistrationBackends = registrationBackends.length > 0;
  const hasAuthBackends = authBackends.length > 0;
  const hasPaymentProvider = paymentBackend.length > 0;
  const hasPrefill = formVariables.some(variable => !!variable.prefillPlugin);

  return [
    hasRegistrationBackends ? 'registrationBackends' : undefined,
    hasPrefill ? 'prefill' : undefined,
    hasPaymentProvider ? 'paymentBackend' : undefined,
    hasAuthBackends ? 'authBackends' : undefined,
  ].filter(Boolean);
};

/**
 * Get a list of options that should be included in the additional form configuration.
 * These options represent additional/supporting parts of the form configuration.
 *
 * The options are based on the form configuration. For example, if the form doesn't have
 * a theme configured, then the theme option is not included.
 *
 * @returns {String[]}
 */
export const useAdditionalFormConfigurationOptions = () => {
  const {components, form} = useContext(FormContext);
  const {authBackends, product, theme, category} = form;

  const hasYiviAttributeGroups = authBackends.some(
    backend =>
      backend.backend === 'yivi_oidc' &&
      (backend.options?.additionalAttributesGroups || []).length > 0
  );
  const hasWMSTileLayers = Object.values(components).some(
    component => component.type === 'map' && (component?.overlays || []).length > 0
  );
  const hasWMTSTileLayers = Object.values(components).some(
    component => component.type === 'map' && !!component?.tileLayerIdentifier
  );

  return [
    Boolean(product) ? 'product' : undefined,
    Boolean(theme) ? 'theme' : undefined,
    Boolean(category) ? 'category' : undefined,
    hasWMSTileLayers ? 'wmsTileLayers' : undefined,
    hasWMTSTileLayers ? 'wmtsTileLayers' : undefined,
    hasYiviAttributeGroups ? 'yiviAttributeGroups' : undefined,
  ].filter(Boolean);
};

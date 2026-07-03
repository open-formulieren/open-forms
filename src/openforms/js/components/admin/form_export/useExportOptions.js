/**
 * Get a list of options that should be included in the form configuration. These options
 * represent key parts of the form configuration.
 *
 * The options are based on the form configuration. For example, if the form doesn't have
 * any registration backends, then the registration backends option is not included.
 *
 * @param {Object} form The form configuration
 * @param {Object[]} registrationBackends The registration backends configured for the form
 * @param {Object[]} formVariables The form variables configured for the form
 * @returns {String[]} A list of form configuration options available for export
 */
export const useFormConfigurationOptions = (form, registrationBackends, formVariables) => {
  const {authBackends, payment} = form;

  const hasRegistrationBackends = registrationBackends.length > 0;
  const hasAuthBackends = authBackends.length > 0;
  const hasPaymentProvider = payment.backend !== '';
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
 * @param {Object} form The form configuration
 * @param {Object} components All components of all form steps used in the form
 * @returns {String[]} A list of additional form configuration options available for
 *   export
 */
export const useAdditionalFormConfigurationOptions = (form, components) => {
  const {authBackends, product} = form;

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
    hasWMSTileLayers ? 'wmsTileLayers' : undefined,
    hasWMTSTileLayers ? 'wmtsTileLayers' : undefined,
    hasYiviAttributeGroups ? 'yiviAttributeGroups' : undefined,
  ].filter(Boolean);
};

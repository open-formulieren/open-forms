/**
 * Convert camelCase export options to snake_case, for API compatibility.
 */
export const serializeExportOptions = exportOptions => ({
  remove_sensitive_content: exportOptions.removeSensitiveContent,
  form_configuration: exportOptions.formConfiguration,
  additional_form_configuration: exportOptions.additionalFormConfiguration,
});

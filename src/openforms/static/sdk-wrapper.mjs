// NOTE - this file must be in the static folder and loaded as type="module", since
// it's intended for modern browsers only and must be ignored by browsers that don't
// natively support modules.

/**
 * Given a form node on the page, extract the options from the data-* attributes and
 * initialize it.
 * @param  {HTMLDivElement} node The root node for the SDK where the form must be
 * rendered. It must have the expected data attributes.
 * @return {Void}
 */
const initializeSDK = async node => {
  const {
    sdkModule,
    formId,
    baseUrl,
    basePath,
    cspNonce,
    sentryDsn = '',
    sentryEnv = '',
  } = node.dataset;
  const {OpenForm} = await import(sdkModule);

  // initialize the SDK
  const options = {
    baseUrl,
    formId,
    basePath,
    CSPNonce: cspNonce,
  };
  if (sentryDsn) options.sentryDSN = sentryDsn;
  if (sentryEnv) options.sentryEnv = sentryEnv;
  const form = new OpenForm(node, options);
  form.init();
};

const sdkNodes = document.querySelectorAll('.open-forms-sdk-root');
sdkNodes.forEach(node => initializeSDK(node));

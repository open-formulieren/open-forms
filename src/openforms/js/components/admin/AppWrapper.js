import React from 'react';
import {IntlProvider} from 'react-intl';

import {getIntlProviderProps} from 'components/admin/i18n';
import jsonScriptToVar from 'utils/json-script';

import {APIContext, FeatureFlagsContext} from './form_design/Context';

export const getWrapperProps = async () => {
  const intlProps = await getIntlProviderProps();
  const featureFlags = jsonScriptToVar('feature-flags', {default: {}});
  return {
    intlProps,
    featureFlags,
  };
};

/**
 * Wraps the useful bit into all the various context providers.
 */
const AppWrapper = ({intlProps, featureFlags, csrftoken = '', strict = true, children}) => {
  const StrictMode = strict ? React.StrictMode : React.Fragment;
  return (
    <StrictMode>
      <IntlProvider {...intlProps}>
        <FeatureFlagsContext.Provider value={featureFlags}>
          <APIContext.Provider value={{csrftoken}}>{children}</APIContext.Provider>
        </FeatureFlagsContext.Provider>
      </IntlProvider>
    </StrictMode>
  );
};

export default AppWrapper;

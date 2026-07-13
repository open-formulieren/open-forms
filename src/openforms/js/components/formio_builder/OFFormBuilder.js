import {FormBuilder} from '@open-formulieren/formio-builder';
import cloneDeep from 'lodash/cloneDeep';
import PropTypes from 'prop-types';
import {useContext, useEffect, useState} from 'react';
import {IntlProvider} from 'react-intl';

import Loader from 'components/admin/Loader';
import {FormContext} from 'components/admin/form_design/Context';
import {getIntlProviderProps} from 'components/admin/i18n';
import {getAvailableAuthPlugins} from 'components/form/cosign';
import {getAvailableDocumentTypes} from 'components/form/file';
import jsonScriptToVar from 'utils/json-script';
import {currentTheme} from 'utils/theme';

import {getMapOverlayTileLayers} from './mapLayers';
import {
  getPrefillAttributes,
  getPrefillPlugins,
  getRegistrationAttributes,
  getValidatorPlugins,
} from './plugins';
import {getReferenceListsTableItems, getReferenceListsTables, getServices} from './referenceLists';

let _supportedLanguages = undefined;
const getSupportedLanguages = () => {
  if (_supportedLanguages !== undefined) return _supportedLanguages;
  _supportedLanguages = jsonScriptToVar('languages', {default: []});
  return _supportedLanguages;
};

const LANGUAGES = getSupportedLanguages().map(([langCode]) => langCode);
const CONFIDENTIALITY_LEVELS = jsonScriptToVar('CONFIDENTIALITY_LEVELS', {default: []});
const FILE_TYPES = jsonScriptToVar('config-UPLOAD_FILETYPES', {default: []});
const MAX_FILE_UPLOAD_SIZE = jsonScriptToVar('setting-MAX_FILE_UPLOAD_SIZE', {default: 'unknown'});
const RICH_TEXT_COLORS = jsonScriptToVar('config-RICH_TEXT_COLORS', {default: []});
const MAP_TILE_LAYERS = jsonScriptToVar('config-MAP_TILE_LAYERS', {default: []});

const OFFormBuilder = ({
  configuration,
  componentNamespace,
  onChange,
  onComponentMutated,
  formDefinitionIdentifier,
}) => {
  const [intlProviderProps, setIntlProviderProps] = useState(null);
  const {
    form: {authBackends = [], type: formType},
    plugins: {availablePrefillPlugins = []},
  } = useContext(FormContext);
  const form = cloneDeep(configuration);

  useEffect(() => {
    async function loadIntlProviderProps() {
      setIntlProviderProps(await getIntlProviderProps());
    }
    if (!intlProviderProps) {
      loadIntlProviderProps();
    }
  }, [intlProviderProps]);

  const uniquifyKey = key => {
    // Copied from formio-builder implementation
    const componentKey = key
      .split(/[^a-zA-Z0-9]/g)
      .filter(Boolean) // Remove empty strings
      .map((str, index) => (index > 0 ? str[0].toUpperCase() + str.slice(1) : str))
      .join('');

    const componentsWithSimilarKeys = componentNamespace
      .filter(component => component.key.startsWith(componentKey))
      .map(component => component.key);
    let index = 0;
    let uniqueKey = componentKey;

    while (componentsWithSimilarKeys.includes(uniqueKey)) {
      index++;
      uniqueKey = `${componentKey}${index}`;
    }
    return uniqueKey;
  };

  if (!intlProviderProps) {
    return <Loader />;
  }

  return (
    <IntlProvider {...intlProviderProps}>
      <FormBuilder
        key={formDefinitionIdentifier}
        components={form?.components ?? []}
        componentNamespace={componentNamespace}
        onChange={formSchema => onChange(cloneDeep(formSchema))}
        onComponentUpdated={(component, originalComponent, isNew) =>
          onComponentMutated('changed', cloneDeep(component), originalComponent, isNew)
        }
        onComponentDeleted={removedComponent =>
          onComponentMutated('removed', cloneDeep(removedComponent))
        }
        // Context binding
        formType={formType}
        uniquifyKey={uniquifyKey}
        supportedLanguageCodes={LANGUAGES}
        theme={currentTheme.getValue()}
        richTextColors={RICH_TEXT_COLORS}
        getMapTileLayers={async () => MAP_TILE_LAYERS}
        getMapOverlayTileLayers={getMapOverlayTileLayers}
        getFormComponents={() => form?.components ?? []}
        getValidatorPlugins={getValidatorPlugins}
        getRegistrationAttributes={getRegistrationAttributes}
        getServices={getServices}
        getReferenceListsTables={getReferenceListsTables}
        getReferenceListsTableItems={getReferenceListsTableItems}
        getPrefillPlugins={getPrefillPlugins}
        getPrefillAttributes={async plugin =>
          await getPrefillAttributes(plugin, {
            authBackends,
            availablePrefillPlugins,
          })
        }
        getFileTypes={async () => FILE_TYPES}
        serverUploadLimit={MAX_FILE_UPLOAD_SIZE}
        getDocumentTypes={async () => await getAvailableDocumentTypes(this)}
        getConfidentialityLevels={async () => CONFIDENTIALITY_LEVELS}
        getAuthPlugins={getAvailableAuthPlugins}
      />
    </IntlProvider>
  );
};

OFFormBuilder.prototype = {
  configuration: PropTypes.object,
  onChange: PropTypes.func,
  onComponentMutated: PropTypes.func,
  componentNamespace: PropTypes.arrayOf(PropTypes.object),
  formDefinitionIdentifier: PropTypes.string,
};

export default OFFormBuilder;

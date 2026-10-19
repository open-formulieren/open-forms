import {FormBuilder as BareFormBuilder} from '@open-formulieren/formio-builder';
import type {MapOverlayTileLayer} from '@open-formulieren/formio-builder/context.js';
import type {AnyComponentSchema, SupportedLocales} from '@open-formulieren/types';
import {useContext, useState} from 'react';
import {useGlobalState} from 'state-pool';

import {FormContext} from '@/components/admin/form_design/Context';
import {
  getAvailableAuthPlugins,
  getPrefillAttributes,
  getPrefillPlugins,
  getRegistrationAttributes,
  getValidatorPlugins,
} from '@/components/admin/form_design/plugins';
import {
  getReferenceListsTableItems,
  getReferenceListsTables,
  getServices,
} from '@/components/admin/form_design/reference-lists';
import {getUniqueKey} from '@/components/admin/form_design/utils';
import {flattenComponents} from '@/components/utils';
import jsonScriptToVar from '@/utils/json-script';
import {currentTheme} from '@/utils/theme';
import type {OFTheme} from '@/utils/theme';

/**
 * A single available language for the application. Tuple made up of language code and
 * language name.
 */
type LanguageDefinition = [SupportedLocales, string];

/**
 * A possible upload file type definition.
 */
interface UploadFileType {
  /**
   * The content type for the file type, e.g. `image/png`. Can also be the wildcard string.
   */
  value: string;
  /**
   * Human readable name for the file type.
   */
  label: string;
}

interface RichTextColor {
  /**
   * Color as HEX code.
   */
  color: `#${string}`;
  /**
   * Human readable color name.
   */
  label: string;
}

interface MapTileLayer {
  identifier: string;
  url: string;
  /**
   * Human readable name for the layer.
   */
  label: string;
}

const LANGUAGES: SupportedLocales[] = jsonScriptToVar<LanguageDefinition[]>('languages', {
  default: [],
}).map(([langCode]) => langCode);

const FILE_TYPES = jsonScriptToVar<UploadFileType[]>('config-UPLOAD_FILETYPES', {default: []});
const MAX_FILE_UPLOAD_SIZE = jsonScriptToVar<string>('setting-MAX_FILE_UPLOAD_SIZE', {
  default: 'unknown',
});

const RICH_TEXT_COLORS = jsonScriptToVar<RichTextColor[]>('config-RICH_TEXT_COLORS', {
  default: [],
});

const MAP_TILE_LAYERS = jsonScriptToVar<MapTileLayer[]>('config-MAP_TILE_LAYERS', {default: []});
const MAP_WMS_LAYERS: MapOverlayTileLayer[] = jsonScriptToVar<Omit<MapOverlayTileLayer, 'type'>[]>(
  'config-MAP_WMS_LAYERS',
  {
    default: [],
  }
).map(layer => ({...layer, type: 'wms'}));
const MAP_WFS_LAYERS: MapOverlayTileLayer[] = [];
const ALL_MAP_OVERLAY_LAYERS = MAP_WMS_LAYERS.concat(MAP_WFS_LAYERS).sort((layerA, layerB) =>
  layerA.name.localeCompare(layerB.name)
);

const VALIDATE_REQUIRED_DEFAULT = jsonScriptToVar<boolean>('config-REQUIRED_DEFAULT', {
  default: false,
});

export const getInitialUsedComponentKeys = (components: AnyComponentSchema[]): string[] => {
  const allComponents = Object.values(flattenComponents(components));
  return allComponents.map(component => component.key);
};

// Strip out spaces and convert to camel case
const toCamelCase = (source: string): string =>
  source
    .split(/[^a-zA-Z0-9]/g)
    .filter(Boolean) // Remove empty strings
    .map((str, index) => (index > 0 ? str[0].toUpperCase() + str.slice(1) : str))
    .join('');

export interface FormBuilderProps {
  initialComponents?: AnyComponentSchema[];
  initialUsedComponentKeys?: string[];
  onChange?: React.ComponentProps<typeof BareFormBuilder>['onChange'];
}

/**
 * Render the form builder UI with component list and form preview.
 *
 * The `FormBuilder` component can be used for formio configuration editing of standalone
 * form definitions, or form definitions that are part of a larger form with one or more
 * form steps.
 *
 * The available component types in the component list depends on the form type being
 * edited. Make sure to set an appropriate `FormContext` parent.
 *
 * Pass the `initialComponents` as a starting point for the configuration. Edits will be
 * reflected through the `onChange` prop, which gives the new configuration and an `event`
 * detailing the nature of changes. Note that the `event` key is absent/`undefined` when
 * components have only been re-ordered without any configuration changes.
 *
 * Careful! If you're looking here because of react-modal warnings about modal instances
 * that cannot be registered that are already open, that warning is safe to ignore! It's
 * because we use React StrictMode, which unmounts-remounts components in development,
 * and react-modal seems to have a race condition triggered in this particular scenario
 * due to delayed/lost state updates. Don't spend hours on this like I did.
 */
const FormBuilder: React.FC<FormBuilderProps> = ({
  initialComponents = [],
  initialUsedComponentKeys = getInitialUsedComponentKeys(initialComponents),
  onChange,
}) => {
  const [components, setComponents] = useState<AnyComponentSchema[]>(initialComponents);
  const [usedComponentKeys, setUsedComponentKeys] = useState<string[]>(initialUsedComponentKeys);
  const {
    form: {authBackends = [], type: formType = 'regular'},
    plugins: {availablePrefillPlugins = []},
  } = useContext(FormContext);
  const [theme] = useGlobalState<OFTheme>(currentTheme);
  return (
    <BareFormBuilder
      components={components}
      onChange={(formSchema, event) => {
        setComponents(formSchema.components);
        onChange?.(formSchema, event);

        // moving components without mutations produces no event
        if (!event) return;

        // update the namespace of used component keys based on the type of change event
        switch (event.type) {
          // creation -> new component key needs to be added
          case 'created': {
            const {component} = event;
            setUsedComponentKeys([...usedComponentKeys, component.key]);
            break;
          }
          // update -> remove old component key and add the new one if the key changed
          case 'updated': {
            const {component, originalComponent} = event;
            if (component.key !== originalComponent.key) {
              const newComponentKeys = usedComponentKeys
                .filter(key => key !== originalComponent.key)
                .concat([component.key]);
              setUsedComponentKeys(newComponentKeys);
            }
            break;
          }
          // delete -> remove the component key entirely
          case 'deleted': {
            const {component} = event;
            setUsedComponentKeys(usedComponentKeys.filter(key => key !== component.key));
            break;
          }
          default: {
            const exhaustiveCheck: never = event;
            throw new Error(`Unknown event ${exhaustiveCheck}`);
          }
        }
      }}
      // Context binding
      validateRequiredDefault={VALIDATE_REQUIRED_DEFAULT}
      formType={formType}
      uniquifyKey={key => getUniqueKey(toCamelCase(key), usedComponentKeys)}
      supportedLanguageCodes={LANGUAGES}
      theme={theme}
      richTextColors={RICH_TEXT_COLORS}
      getMapTileLayers={async () => MAP_TILE_LAYERS}
      getMapOverlayTileLayers={async () => ALL_MAP_OVERLAY_LAYERS}
      getFormComponents={() => components}
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
      getAuthPlugins={getAvailableAuthPlugins}
    />
  );
};

FormBuilder.displayName = 'FormBuilder';

export default FormBuilder;

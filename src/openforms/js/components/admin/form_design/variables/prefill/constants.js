import DefaultFields from './default/DefaultFields';
import ObjectsAPIFields from './objects_api/ObjectsAPIFields';
import ToggleCopyButton from './objects_api/ToggleCopyButton';

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: {
    component: ObjectsAPIFields,
    pluginFieldExtra: ToggleCopyButton,
  },
  default: {
    component: DefaultFields,
    pluginFieldExtra: null,
  },
};

export default PLUGIN_COMPONENT_MAPPING;

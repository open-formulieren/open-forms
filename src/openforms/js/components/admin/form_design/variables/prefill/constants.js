import DefaultFields from './default/DefaultFields';
import ObjectsAPIFields from './objects_api/ObjectsAPIFields';
import ToggleCopyButton from './objects_api/ToggleCopyButton';

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: {component: ObjectsAPIFields, toggleCopyComponent: ToggleCopyButton},
  default: {component: DefaultFields, toggleCopyComponent: null},
};

export default PLUGIN_COMPONENT_MAPPING;

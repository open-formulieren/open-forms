import DefaultFields from './default/DefaultFields';
import FamilyMembersFields from './family_members/FamilyMembersFields';
import KlantinteractiesFields from './klantinteracties/KlantinteractiesFields';
import ObjectsAPIFields from './objects_api/ObjectsAPIFields';
import ToggleCopyButton from './objects_api/ToggleCopyButton';
import YiviFields from './yivi/YiviFields';

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: {
    component: ObjectsAPIFields,
    pluginFieldExtra: ToggleCopyButton,
  },
  family_members: {
    component: FamilyMembersFields,
    pluginFieldExtra: null,
  },
  yivi: {
    component: YiviFields,
    pluginFieldExtra: null,
  },
  klantinteracties: {
    component: KlantinteractiesFields,
    pluginFieldExtra: null,
  },
  default: {
    component: DefaultFields,
    pluginFieldExtra: null,
  },
};

export default PLUGIN_COMPONENT_MAPPING;

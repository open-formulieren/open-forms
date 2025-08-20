import DefaultFields from './default/DefaultFields';
import EidasFields from './eidas/EidasFields';
import EidasCompanyFields from './eidas_company/EidasCompanyFields';
import FamilyMembersFields from './family_members/FamilyMembersFields';
import ObjectsAPIFields from './objects_api/ObjectsAPIFields';
import ToggleCopyButton from './objects_api/ToggleCopyButton';

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: {
    component: ObjectsAPIFields,
    pluginFieldExtra: ToggleCopyButton,
  },
  family_members: {
    component: FamilyMembersFields,
    pluginFieldExtra: null,
  },
  eidas: {
    component: EidasFields,
    pluginFieldExtra: null,
  },
  eidas_company: {
    component: EidasCompanyFields,
    pluginFieldExtra: null,
  },
  default: {
    component: DefaultFields,
    pluginFieldExtra: null,
  },
};

export default PLUGIN_COMPONENT_MAPPING;

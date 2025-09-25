import jsonScriptToVar from 'utils/json-script';

const MAP_WMS_LAYERS = jsonScriptToVar('config-MAP_WMS_LAYERS', {default: []});
const MAP_WFS_LAYERS = [];

export const getMapOverlayTileLayers = async () => {
  const layers = [
    ...MAP_WMS_LAYERS.map(layer => ({...layer, type: 'wms'})),
    ...MAP_WFS_LAYERS.map(layer => ({...layer, type: 'wfs'})),
  ];
  return layers.sort((layerA, layerB) => layerA.name.localeCompare(layerB.name));
};

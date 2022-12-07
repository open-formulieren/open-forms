import {Formio} from 'formiojs';

const getComponentEmptyValue = component => {
  const componentInstance = Formio.Components.create(component);
  return componentInstance.emptyValue;
};

export {getComponentEmptyValue};

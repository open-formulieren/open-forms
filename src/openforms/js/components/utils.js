import FormIOModule from 'formio_module';

const getComponentEmptyValue = component => {
  const componentClasses = FormIOModule.components;
  const componentInstance = new componentClasses[component.type]();
  return componentInstance.emptyValue;
};

export {getComponentEmptyValue};

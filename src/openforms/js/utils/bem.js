import classNames from 'classnames';

export const getBEMClassName = (base, modifiers=[]) => {
  const prefixedModifiers = modifiers.map(mod => `${base}--${mod}`);
  return classNames(base, ...prefixedModifiers);
};

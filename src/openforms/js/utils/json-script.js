const jsonScriptToVar = (elementId, options = {}) => {
  const node = document.getElementById(elementId);

  if (!node && options.default !== undefined) return options.default;

  const content = node.innerText;
  return JSON.parse(content);
};

export default jsonScriptToVar;

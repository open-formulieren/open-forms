interface JsonScriptToVarOptions<T = unknown> {
  default?: T;
}

const jsonScriptToVar = <T = unknown>(
  elementId: string,
  options: JsonScriptToVarOptions<T> = {}
): T => {
  const node = document.getElementById(elementId);
  if (!node) {
    if (options.default !== undefined) return options.default;
    throw new Error(`No node found for ID '${elementId}' and no default provided!`);
  }
  const content = node.innerText;
  return JSON.parse(content);
};

export default jsonScriptToVar;

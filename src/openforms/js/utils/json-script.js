const jsonScriptToVar = (elementId) => {
    const node = document.getElementById(elementId);
    const content = node.innerText;
    return JSON.parse(content);
};


export default jsonScriptToVar;

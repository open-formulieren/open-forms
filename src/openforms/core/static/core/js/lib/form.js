/**
 * Takes form and serializes it's value to a plain Object.
 * @param {HTMLFormElement} form The <form> to serialize.
 * @return {Object} Key/value pairs for every input in "form".
 */
export const serializeForm = (form) => {
    const data = {};
    const formData = new FormData(form);

    formData.forEach((value, key) => {
        // Key not yet set on data, set value.
        if (!data.hasOwnProperty(key)) {
            data[key] = value;
            return;
        }

        // Key already set on data, turn into Array.
        if (!Array.isArray(data[key])) {
            data[key] = [data[key]];
        }

        // Key is known to be Array, push value.
        data[key].push(value);
    });

    return data;
};

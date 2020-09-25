/**
 * Recurses through a complex Object "object" seeking for primitive values and returns an Array[] where each item
 * contains:
 *
 * - [0]: The absolute path from "object" to the final primitive value.
 * - [1]: The key of primitive value within the latest nested object.
 * - [2]: The primitive value.
 *
 * This is useful for searching for certain values and or paths in a complex object.
 *
 * @example
 *
 * const haystack = {
 *   foo: "bar",
 *   myArray: [
 *     {
 *       bar: 1,
 *       myObj: {
 *         baz: true,
 *         needle: "Got it!",
 *       }
 *     }
 *   ]
 * }
 *
 * recurse(haystack)[3]  // [".myArray.[0].myObj.needle", "needle", "Got it!"]
 *
 * recurse(haystack)
 *   .find(([key, value]) => key.match("\.needle$"))[2]  // "Got it!"
 *
 * @param {*} object The input object, can be of any type.
 * @param {string} _path Private, The current recursor's path to "object"
 * @param {Array[]} _result Private, the current recursor's result.
 *
 * @return {Array[]} Array of Arrays where each item contains:
 *
 * - [0]: The absolute path from "object" to the final primitive value.
 * - [1]: The key of primitive value within the latest nested object.
 * - [2]: The primitive value.
 */
export const recurse = (object, _path = '', _result = []) => {
    const isObject = Object.prototype.toString.call(object) === '[object Object]';
    const isArray = Array.isArray(object);

    // Array (branch)
    if (isArray) {
        object.map((o, i) => {
            _result = recurse(o, `${_path}.[${i}]`, _result);
        });
    }

    // Object (branch)
    else if (isObject) {
        Object.entries(object).forEach(o => {
            const [key, value] = o;
            _result = recurse(value, `${_path}.${key}`, _result);
        });
    }

    // Assume primitive, (leaf)
    else {
        const key = _path.split(".").slice(-1)[0];
        _result.push([_path, key, object]);
    }

    return _result;
};

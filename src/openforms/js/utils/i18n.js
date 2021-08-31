/**
 * Given a list of choices with defined messages, ensure the list of translated choices
 * is returned.
 *
 * @param {Object|Array} choices An object or array of choices. Objects are normalized
 *   to an array of [value, label] choices.
 */
const getTranslatedChoices = (intl, choices) => {
    let choicesArray;
    if (!Array.isArray(choices)) {
        choicesArray = Object.entries(choices);
    } else {
        choicesArray = choices;
    }
    return choicesArray.map( ([value, labelMessage]) => [value, intl.formatMessage(labelMessage)] );
};

export {getTranslatedChoices};

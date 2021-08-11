const fs = require('fs');
const argv = require('yargs').argv;

// load the existing catalog to prevent overwriting messages
const existingCatalog = JSON.parse(
    fs.readFileSync(argv.outFile, 'utf-8')
);


const format = (messages) => {
    Object.entries(messages).forEach(([id, msg]) => {
        // always store the original (english) default message as a reference
        msg.originalDefault = msg.defaultMessage;

        // if the message with the ID is already in the catalog, re-use it
        const existingMsg = existingCatalog[id];
        if (!existingMsg) return;
        msg.defaultMessage = existingMsg.defaultMessage;
    });
    return messages;
};

exports.format = format;

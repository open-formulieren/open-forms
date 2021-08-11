const fs = require('fs');
const argv = require('yargs').argv;

const COMPILED_MSG_DIR = 'src/openforms/js/compiled-lang';

// determine which existing translations to load
// const outFilename = argv.outFile.split('/').pop();

const existingCatalog = JSON.parse(
    fs.readFileSync(argv.outFile, 'utf-8')
);


const format = (messages) => {
    Object.entries(messages).forEach(([id, msg]) => {
        // if the message with the ID is already in the catalog, re-use it
        const existingMsg = existingCatalog[id];
        if (!existingMsg) return;
        msg.defaultMessage = existingMsg.defaultMessage;
    });
    return messages;
};

exports.format = format;

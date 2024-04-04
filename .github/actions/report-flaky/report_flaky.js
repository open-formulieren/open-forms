// Taken from: https://nodejs.org/api/readline.html#readline_example_read_file_stream_line_by_line
const fs = require('node:fs');
const readline = require('node:readline');

const core = require('@actions/core');

const logFilePath = core.getInput('logFile');

async function emitAnnotations() {
  const fileStream = fs.createReadStream(logFilePath);

  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity,
  });
  // Note: we use the crlfDelay option to recognize all instances of CR LF
  // ('\r\n') in input.txt as a single line break.

  for await (const line of rl) {
    // each line is expected to be valid JSON
    const logRecord = JSON.parse(line);
    core.warning(logRecord.msg, {file: logRecord.file, startLine: logRecord.line});
  }
}

emitAnnotations();

import { SaveDocument } from '../web/save-core.js';
let text = '';
for await (const chunk of process.stdin) text += chunk;
const request = JSON.parse(text);
const save = new SaveDocument(Buffer.from(request.bytes, 'base64'));
save.setCalendar(request.calendar);
for (const flag of request.flags) save.setFlag(flag, flag.value);
process.stdout.write(JSON.stringify({ output: Buffer.from(save.build()).toString('base64'), values: request.flags.map(flag => save.flag(flag)) }));

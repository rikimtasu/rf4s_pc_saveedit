import { MarriageEditor, MARRIAGE_CANDIDATES, MARRIAGE_FIELDS } from './marriage-core.js';
import { SEASONS } from './save-core.js';

const $ = id => document.getElementById(id);
export class MarriageUI {
  constructor({ getSave, getSymbols, personName, changed, draftChanged, notify }) {
    Object.assign(this, { getSave, getSymbols, personName, changed, draftChanged, notify });
    this.drafts = new Map(); this.candidate = 1;
    for (const { key } of MARRIAGE_FIELDS) this.bind(key);
    for (const key of ['marriageEvent', 'newlywedEvent']) this.bind(key);
    $('marriage-candidate').addEventListener('change', event => {
      if (this.pending()) { event.target.value = this.candidate; this.notify('Apply or clear marriage drafts before switching candidates.', true); return; }
      this.candidate = Number(event.target.value); this.render();
    });
    $('allow-marriage').addEventListener('change', () => { this.render(); this.draftChanged(); });
    $('clear-marriage').addEventListener('click', () => { this.drafts.clear(); this.render(); this.draftChanged(); });
    $('marriage-form').addEventListener('submit', event => {
      event.preventDefault();
      try {
        if (!this.slot() || !$('allow-marriage').checked) throw new Error('Enable marriage editing first.');
        this.editor().apply(Object.fromEntries(this.drafts), this.candidate);
        this.drafts.clear(); this.changed('Marriage flags applied as one undoable edit. Wedding events, children and system unlocks were not simulated.');
      } catch (error) { this.notify(error.message, true); }
    });
  }
  slot() { return this.getSave()?.kind === 'slot'; }
  editor() { return new MarriageEditor(this.getSave(), this.getSymbols()); }
  validateSymbols(symbols) {
    const editor = new MarriageEditor(this.getSave(), symbols);
    for (const field of MARRIAGE_FIELDS) editor.field(field.name);
    for (const candidate of MARRIAGE_CANDIDATES) editor.eventFields(candidate.id);
  }
  pending() { return this.drafts.size > 0; }
  clear() { this.drafts.clear(); $('allow-marriage').checked = false; }
  current() { return this.slot() ? { ...this.editor().values(), ...this.editor().events(this.candidate) } : {}; }
  bind(key) {
    const input = $(`marriage-${key}`);
    input.addEventListener(input.type === 'checkbox' || input.tagName === 'SELECT' ? 'change' : 'input', () => {
      const value = input.type === 'checkbox' ? Number(input.checked) : input.value;
      if (value !== '' && Number(value) === this.current()[key]) this.drafts.delete(key);
      else this.drafts.set(key, value);
      this.note(); this.draftChanged();
    });
  }
  note() { $('marriage-note').textContent = this.pending() ? 'Marriage draft pending · apply or clear before export' : 'Edits only the selected flags. This is not a complete marry / divorce operation.'; }
  render() {
    $('allow-marriage').disabled = !this.slot();
    $('marriage-fields').disabled = !this.slot() || !$('allow-marriage').checked;
    const candidates = MARRIAGE_CANDIDATES.map(person => new Option(this.personName(person.id, person.name), person.id));
    $('marriage-candidate').replaceChildren(...candidates); $('marriage-candidate').value = this.candidate;
    const current = this.current();
    const spouse = this.drafts.get('spouse') ?? current.spouse ?? 0;
    $('marriage-spouse').replaceChildren(new Option('None · 0', 0), ...MARRIAGE_CANDIDATES.map(person => new Option(this.personName(person.id, person.name), person.id)));
    if (![0, ...MARRIAGE_CANDIDATES.map(person => person.id)].includes(Number(spouse))) $('marriage-spouse').append(new Option(`Unrecognized stored ID ${spouse} · keep unless verified`, spouse));
    $('marriage-season').replaceChildren(...SEASONS.map((season, index) => new Option(season, index)));
    for (const key of [...MARRIAGE_FIELDS.map(field => field.key), 'marriageEvent', 'newlywedEvent']) {
      const input = $(`marriage-${key}`); const value = this.drafts.get(key) ?? current[key] ?? '';
      if (input.type === 'checkbox') input.checked = Number(value) === 1;
      else input.value = value;
    }
    const person = MARRIAGE_CANDIDATES.find(person => person.id === current.spouse);
    $('marriage-summary').textContent = !this.slot() ? 'Open a slot save' : `${current.spouse === 0 ? 'No spouse recorded' : person ? this.personName(person.id, person.name) : `Unrecognized spouse ID ${current.spouse}`} · anniversary ${SEASONS[current.season]} ${current.day || '(unset)'}`;
    this.note();
  }
}

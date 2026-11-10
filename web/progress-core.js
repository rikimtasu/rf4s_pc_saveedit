import { integer, STORY_REGISTER } from './save-core.js';
import { STORY_WITNESSES } from './flag-help.js';

export const STORY_MARKERS = STORY_WITNESSES.map(witness => ({ value: witness.value, label: `${witness.en} · script evidence` }));

export function progressGroup(variable) {
  if (['Story Event Flags', 'Other Event Flags'].includes(variable.group)) return 'Main story';
  if (variable.group) return variable.group;
  if (/SUBEV/.test(variable.name)) return 'Town events';
  if (/QUEST|REQUEST|ELIZA/.test(variable.name)) return 'Requests';
  if (/MAIN|SCENARIO/.test(variable.name)) return 'Main story';
  return 'Other developer flags';
}

export class ProgressCatalog {
  constructor(symbols, aliases = []) {
    this.variables = symbols.map(variable => ({ ...variable, group: progressGroup(variable) }));
    const bits = new Map();
    const names = new Set();
    for (const variable of this.variables) {
      if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(variable.name) || names.has(variable.name)) throw new Error('Invalid or duplicate progress symbol.');
      integer(variable.width, 1, 32, 'Flag width');
      integer(variable.bitOffset, 0, 4096 - variable.width, 'Named flag offset');
      for (let bit = variable.bitOffset; bit < variable.bitOffset + variable.width; bit++) {
        if (bits.has(bit)) throw new Error('Developer progress symbols overlap.');
        bits.set(bit, variable);
      }
      names.add(variable.name);
    }
    const main = this.variables.find(variable => variable.name === STORY_REGISTER.name);
    if (!main || main.bitOffset !== 0 || main.width !== 9) throw new Error('Unexpected main-story register.');
    for (const alias of aliases) {
      integer(alias.bitOffset, 0, 6655, 'Reference flag offset');
      if (alias.width !== 1) throw new Error('Only verified single-bit CT aliases are supported.');
      const existing = bits.get(alias.bitOffset);
      if (existing) {
        if (existing.width !== 1 || existing.name !== alias.name) throw new Error('CT alias conflicts with a developer register.');
        existing.label = alias.label;
        existing.referenceGroup = alias.group;
        existing.source = alias.source;
      } else {
        if (names.has(alias.name)) throw new Error('Duplicate CT reference symbol.');
        const variable = { ...alias };
        this.variables.push(variable);
        bits.set(alias.bitOffset, variable);
        names.add(alias.name);
      }
    }
    this.byName = new Map(this.variables.map(variable => [variable.name, variable]));
  }

  entries(values) {
    if (!values || typeof values !== 'object' || Array.isArray(values)) throw new Error('A progress profile must contain a flag-value object.');
    return Object.entries(values).map(([name, input]) => {
      const variable = this.byName.get(name);
      if (!variable) throw new Error(`Unknown progress symbol: ${name}.`);
      return { variable, value: integer(input, 0, 2 ** variable.width - 1, name) };
    });
  }

  snapshot(save, scope = 'all') {
    save.requireSlot();
    if (!['all', 'story', 'quests'].includes(scope)) throw new Error('Unknown progress-profile scope.');
    const variables = this.variables.filter(variable => scope === 'all' || scope === 'story' && (progressGroup(variable) === 'Main story' || /Story Barrier|Dungeon Barrier/.test(variable.referenceGroup || variable.group)) || scope === 'quests' && ['Requests', 'Town events'].includes(progressGroup(variable)));
    return Object.fromEntries(variables.map(variable => [variable.name, save.flag(variable)]));
  }

  parseProfile(text) {
    const profile = JSON.parse(text);
    if (profile.format !== 'rf4s-progress-v1') throw new Error('Expected an rf4s-progress-v1 JSON profile.');
    const entries = this.entries(profile.flags);
    if (!entries.length) throw new Error('The progress profile is empty.');
    return { label: String(profile.label || 'Imported progress profile').slice(0, 120), entries };
  }
}

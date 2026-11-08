import { SaveDocument, createDemo, parseEmdeb, STORY_REGISTER, SEASONS, SAVE_SIZE, SWITCH_SAVE_SIZE, SYSTEM_SAVE_SIZE, SWITCH_CRC_END, CRC_END, SYSTEM_FLAGS, NUMBER_TYPES, PLAYER_FIELDS, INVENTORIES, ITEM_RECORD_SIZE, bagStackLimit, hex, equalBytes, integer } from './save-core.js';
import { VENTI_TABLES } from './game-schema.js';
import { ItemCatalog, ItemTable, ITEM_GROUPS, detectItemTable, categoryName, decodeItemFlags, semanticValue } from './game-reference.js';
import { LOCAL_GAME_DATA } from './local-game-data.js';
import { SAVE_METADATA } from './save-metadata.js';
import { ProgressCatalog, STORY_MARKERS, progressGroup } from './progress-core.js';
import { ExtendedUI } from './extended-ui.js';
import { SaveReferences } from './save-reference.js';
import { LOCAL_SAVE_REFERENCE } from './local-save-reference.js';

const $ = id => document.getElementById(id);
const bytesText = bytes => Array.from(bytes, byte => byte.toString(16).toUpperCase().padStart(2, '0')).join(' ');
let save;
let demo = false;
let progressCatalog = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
let symbols = progressCatalog.variables;
let storyValueDraft;
let profileDraft;
let flagPage = 0;
let pendingReplacement;
let lastExport;
let loading = false;
const flagDrafts = new Map();
const playerDrafts = new Map();
const bagDrafts = new Map();
let bagSlot = 0;
let bagPage = 0;
const BAG_PAGE_SIZE = 10;
const PAGE_SIZE = 8;
const catalog = new ItemCatalog(LOCAL_GAME_DATA);
const extraUi = new ExtendedUI({ getSave: () => save, references: new SaveReferences(LOCAL_SAVE_REFERENCE), itemName: id => catalog.name(id), changed: message => { render(); notify(message); }, draftChanged: updateExportButton, notify });
const words = value => String(value).replace(/([a-z])([A-Z])/g, '$1 $2').replaceAll('_', ' ').toLowerCase().replace(/^./, char => char.toUpperCase());
const slotSave = () => save?.kind === 'slot';
const selectedContainer = () => $('bag-container').value;
const inventoryItems = () => save.inventoryItems(selectedContainer());
const inventorySlot = (slot, bytes) => save.inventorySlot(selectedContainer(), slot, bytes);

function notify(message, warning = false) {
  $('notice').textContent = message;
  $('notice').classList.toggle('warning', warning);
}

function attempt(action) {
  try { return action(); } catch (error) { notify(error.message, true); return false; }
}

function hasUnexportedEdits() {
  return save && save.dirty && (!lastExport || !equalBytes(save.data, lastExport));
}

function dateDraft() {
  return slotSave() && (Number($('day').value) !== save.get('day') || Number($('season').value) !== save.get('season') || Number($('year').value) !== save.get('year'));
}

function pendingDrafts() {
  return extraUi.pending() || dateDraft() || storyValueDraft !== undefined || Boolean(profileDraft) || flagDrafts.size > 0 || playerDrafts.size > 0 || bagDrafts.size > 0 || (save && $('allow-raw').checked && ($('raw-value').value.trim() || $('typed-value').value.trim()));
}

function exportFilename() {
  const base = save.name.replace(/\.sav$/i, '').replace(/[<>:"/\\|?*\x00-\x1f]/g, '_');
  const target = $('export-platform').value;
  return `${base}${save.platform !== target ? `.${target}` : ''}.edited.sav`;
}

function conversionIssue() {
  if (!save || $('export-platform').value === save.platform) return '';
  if (!$('allow-conversion').checked) return 'Acknowledge experimental conversion before exporting.';
  if (!save.playerProfile) return 'Conversion requires recognized player values.';
  if (save.platform === 'pc' && save.data.subarray(SWITCH_CRC_END, CRC_END).some(byte => byte !== 0)) return 'Conversion blocked: the eight-byte PC-only region is not empty.';
  return '';
}

function exportOptions(repair = $('repair-crc').checked) {
  const correctGender = slotSave() && $('correct-gender').checked;
  return { repair, platform: $('export-platform').value, experimental: $('allow-conversion').checked, gender: correctGender ? $('export-gender').value : 'keep', resetAppearance: correctGender && $('reset-appearance').checked };
}

function genderIssue() {
  if (!save) return '';
  try { const options = exportOptions(); save.genderCorrection(options.gender, options.resetAppearance); return ''; }
  catch (error) { return error.message; }
}

function updateExportButton() {
  const playerIssues = save?.playerProfile ? save.playerIssues() : [];
  const allowed = save && !demo && !save.calendarIssues().length && !playerIssues.length && !conversionIssue() && !genderIssue() && (save.crcValid || $('repair-crc').checked) && !pendingDrafts();
  $('export-save').disabled = !allowed;
  $('export-save').title = pendingDrafts() ? 'Apply or clear draft fields before exporting.' : conversionIssue() || genderIssue() || playerIssues.join(' ');
  $('expert-drafts').hidden = !expertDrafts();
}

function expertDrafts() {
  return storyValueDraft !== undefined || Boolean(profileDraft) || flagDrafts.size > 0 || (save && $('allow-raw').checked && ($('raw-value').value.trim() || $('typed-value').value.trim()));
}

function fillCalendar() {
  for (const option of $('season').querySelectorAll('[data-invalid]')) option.remove();
  for (const name of ['day', 'season', 'year']) $(name).value = slotSave() ? save.get(name) : (name === 'season' ? 0 : '');
  if (slotSave() && save.get('season') > 3) {
    const option = new Option(`Invalid (${save.get('season')})`, String(save.get('season')));
    option.dataset.invalid = 'true';
    $('season').append(option);
    $('season').value = save.get('season');
  }
  updateDatePreview();
}

function updateDatePreview() {
  const day = $('day').value;
  const season = SEASONS[Number($('season').value)];
  const year = $('year').value;
  $('calendar-preview').textContent = slotSave() ? (dateDraft() ? 'Unapplied date · apply before export' : `${season || 'Invalid season'} ${day} · Year ${year}`) : 'No slot save loaded';
  updateExportButton();
}

function renderFlags() {
  const flagSave = slotSave() ? save : null;
  const query = $('flag-search').value.trim().toLowerCase();
  const mode = $('flag-filter').value;
  const filtered = symbols.filter(variable => {
    if (!`${variable.name} ${variable.label || ''} ${variable.description || ''}`.toLowerCase().includes(query)) return false;
    const group = $('flag-group').value;
    const category = progressGroup(variable);
    if (group === 'story' && category !== 'Main story') return false;
    if (group === 'quests' && category !== 'Requests') return false;
    if (group === 'town' && category !== 'Town events') return false;
    if (group === 'barriers' && !/Barrier/.test(variable.referenceGroup || variable.group)) return false;
    if (group === 'ct' && !variable.source) return false;
    if (mode === 'flags') return variable.width === 1;
    if (mode === 'registers') return variable.width > 1;
    if (mode === 'changed') return flagSave && flagSave.flag(variable) !== flagSave.flag(variable, flagSave.original);
    return true;
  });
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  flagPage = Math.max(0, Math.min(flagPage, pages - 1));
  $('flag-list').replaceChildren();
  const enabled = flagSave && $('allow-flags').checked;
  for (const variable of filtered.slice(flagPage * PAGE_SIZE, (flagPage + 1) * PAGE_SIZE)) {
    const current = flagSave ? flagSave.flag(variable) : undefined;
    const original = flagSave ? flagSave.flag(variable, flagSave.original) : undefined;
    const row = document.createElement('div');
    row.className = `flag-row${current !== original ? ' changed' : ''}`;
    const info = document.createElement('div');
    info.className = 'flag-info';
    const name = document.createElement('code');
    name.textContent = variable.name;
    const meta = document.createElement('span');
    meta.className = 'flag-meta';
    meta.textContent = `Bit ${variable.bitOffset} · ${variable.width === 1 ? '1-bit flag' : `${variable.width}-bit register`} · 0–${(2 ** variable.width - 1).toLocaleString()}${current !== original ? ` · was ${original}` : ''}`;
    info.append(name, meta);
    if (variable.label || variable.description) {
      const label = document.createElement('span');
      label.className = 'flag-meta';
      label.textContent = `${variable.label || variable.description}${variable.source ? ' · CT reference' : ''}`;
      info.append(label);
    }
    const controls = document.createElement('div');
    controls.className = 'flag-control';
    const input = document.createElement('input');
    input.setAttribute('aria-label', variable.name);
    input.disabled = !enabled;
    const commit = value => attempt(() => {
      if (!slotSave() || !$('allow-flags').checked) throw new Error('Enable story editing first.');
      save.setFlag(variable, value);
      flagDrafts.delete(variable.name);
      render();
      notify(`Applied ${variable.name}.`);
    });
    if (variable.width === 1) {
      input.type = 'checkbox';
      input.checked = current === 1;
      input.addEventListener('change', () => { if (commit(input.checked ? 1 : 0) === false) renderFlags(); });
      controls.append(input);
    } else {
      input.type = 'number';
      input.min = 0;
      input.max = 2 ** variable.width - 1;
      input.step = 1;
      input.value = flagDrafts.get(variable.name) ?? current ?? '';
      input.placeholder = '—';
      input.addEventListener('input', () => {
        if (input.value !== '' && Number(input.value) === current) flagDrafts.delete(variable.name);
        else flagDrafts.set(variable.name, input.value);
        updateExportButton();
      });
      const apply = document.createElement('button');
      apply.type = 'button';
      apply.disabled = !enabled;
      apply.setAttribute('aria-label', `Apply ${variable.name}`);
      apply.innerHTML = '<i class="ti ti-check" aria-hidden="true"></i>';
      apply.addEventListener('click', () => commit(input.value));
      input.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); commit(input.value); } });
      controls.append(input, apply);
    }
    row.append(info, controls);
    $('flag-list').append(row);
  }
  if (!filtered.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'No matching symbols';
    $('flag-list').append(empty);
  }
  $('flag-result-count').textContent = `${filtered.length.toLocaleString()} ${filtered.length === 1 ? 'symbol' : 'symbols'}`;
  $('flag-page').textContent = `${flagPage + 1} / ${pages}`;
  $('flag-prev').disabled = flagPage === 0;
  $('flag-next').disabled = flagPage >= pages - 1;
  $('symbol-count').textContent = `${symbols.length.toLocaleString()} ${symbols.length === 1 ? 'known register' : 'symbols loaded'}`;
}

function renderHex() {
  if (!save) return;
  attempt(() => {
    const offset = integer($('raw-offset').value, 0, save.size - 1, 'Offset');
    const start = Math.floor(offset / 16) * 16;
    const lines = [];
    for (let pos = start; pos < Math.min(start + 64, save.size); pos += 16) {
      const bytes = [];
      for (let index = pos; index < Math.min(pos + 16, save.size); index++) {
        const value = save.data[index].toString(16).toUpperCase().padStart(2, '0');
        bytes.push(save.data[index] !== save.original[index] ? `<span class="hex-changed">${value}</span>` : value);
      }
      lines.push(`${hex(pos)}  ${bytes.join(' ')}`);
    }
    $('hex-view').innerHTML = lines.join('\n');
  });
}

function renderChanges() {
  const ranges = save ? save.changes() : [];
  if (!ranges.length) {
    $('change-list').innerHTML = `<div class="empty-state"><i class="ti ti-file-check" aria-hidden="true"></i><span>${save && !save.crcValid ? 'Checksum repair only' : 'No edits yet'}</span></div>`;
    return;
  }
  $('change-list').innerHTML = ranges.map(range => {
    const limit = 24;
    const suffix = range.before.length > limit ? ` … (${range.before.length} bytes)` : '';
    return `<div class="change-row"><code>${hex(range.offset)}</code><div class="change-bytes"><span class="change-before">${bytesText(range.before.slice(0, limit))}${suffix}</span><br><span class="change-after">${bytesText(range.after.slice(0, limit))}${suffix}</span></div></div>`;
  }).join('');
}

function referenceFields() {
  const type = $('reference-table').value;
  $('reference-field').replaceChildren(...Object.keys(VENTI_TABLES[type].fields).map(field => new Option(words(field), field)));
  renderReference();
}

function renderReference() {
  $('use-reference-id').disabled = !save || !$('allow-raw').checked;
  const type = $('reference-table').value;
  const field = $('reference-field').value;
  const count = catalog.count(type);
  $('reference-source').textContent = catalog.tables.size ? 'Imported reference tables · read only' : LOCAL_GAME_DATA ? 'Your game copy · read only' : 'Vanilla name registry';
  $('reference-count').textContent = count === undefined ? 'Source table not loaded' : `${count.toLocaleString()} definition records`;
  $('reference-field').title = VENTI_TABLES[type].fields[field]?.description || '';
  $('reference-item-name').textContent = 'Invalid reference ID';
  for (const id of ['reference-category', 'reference-prices', 'reference-rarity']) $(id).textContent = '—';
  try {
    const id = integer($('reference-item-id').value, 0, 0xffffffff, 'Reference item ID');
    $('reference-item-name').textContent = catalog.name(id);
    const item = catalog.record('item', id);
    $('reference-category').textContent = item ? words(categoryName(item.category)) : 'Not loaded';
    $('reference-prices').textContent = item ? `${item.buy.toLocaleString()} / ${item.sell.toLocaleString()}` : 'Not loaded';
    $('reference-rarity').textContent = item ? `${item.rarity} / ${item.max_stack}` : 'Not loaded';
    const record = catalog.record(type, id);
    $('reference-value').textContent = record ? field === 'flags' && type === 'item' ? `${record[field]} · ${decodeItemFlags(record[field])}` : String(record[field]) : 'Not loaded';
  } catch (error) {
    $('reference-value').textContent = 'Outside reference table';
  }
}

function renderTyped() {
  $('typed-fields').disabled = !save || !$('allow-raw').checked;
  const spec = NUMBER_TYPES[$('typed-type').value];
  $('typed-range').textContent = `${spec.min.toLocaleString()}–${spec.max.toLocaleString()}`;
  $('typed-current').textContent = '—';
  $('typed-decoded').textContent = '';
  if (!save || !$('typed-offset').value.trim()) return;
  try {
    const value = save.readNumber($('typed-offset').value, $('typed-type').value);
    $('typed-current').textContent = String(value);
    const meaning = $('typed-meaning').value;
    $('typed-decoded').textContent = meaning === 'item' ? catalog.name(value) : meaning === 'category' ? words(categoryName(value)) : meaning === 'flags' ? decodeItemFlags(value) : '';
  } catch { $('typed-current').textContent = 'Invalid offset'; }
}

function setupPlayer() {
  const groups = [
    { label: 'Money and order points', fields: ['money', 'prince_points'] },
    { label: 'Materials', fields: ['lumber', 'material_stone', 'fertilizer'] },
    { label: 'Health and rune points', fields: ['max_hp', 'hp', 'max_rp', 'rp'] },
    { label: 'Base attributes', fields: ['strength', 'intelligence', 'vitality'] },
  ];
  const remaining = Object.keys(PLAYER_FIELDS).filter(name => !groups.some(group => group.fields.includes(name)));
  if (remaining.length) groups.push({ label: 'Other values', fields: remaining });
  const inputs = new Map();
  for (const [name, spec] of Object.entries(PLAYER_FIELDS)) {
    const label = document.createElement('label');
    label.append(spec.label);
    const input = document.createElement('input');
    input.id = `player-${name}`;
    input.type = 'number';
    input.min = spec.min;
    input.max = spec.max;
    input.step = 1;
    input.required = true;
    input.addEventListener('input', () => {
      if (slotSave() && input.value !== '' && Number(input.value) === save.player(name)) playerDrafts.delete(name);
      else playerDrafts.set(name, input.value);
      updatePlayerPreview();
      updateExportButton();
    });
    input.title = `${spec.min.toLocaleString()}–${spec.max.toLocaleString()}`;
    label.append(input);
    if (name === 'prince_points') {
      const hint = document.createElement('span');
      hint.className = 'field-hint';
      hint.textContent = 'Prince/princess points · up to 99,999';
      label.append(hint);
    }
    inputs.set(name, label);
  }
  for (const group of groups) {
    const section = document.createElement('div');
    section.className = 'player-group';
    const title = document.createElement('h3');
    title.textContent = group.label;
    const grid = document.createElement('div');
    grid.className = `form-grid${group.fields.length === 2 || group.fields.length === 4 ? ' paired-grid' : ''}`;
    grid.append(...group.fields.map(name => inputs.get(name)));
    section.append(title, grid);
    $('player-inputs').append(section);
  }
}

function updatePlayerPreview() {
  const issues = slotSave() ? save.playerIssues() : [];
  $('player-preview').textContent = !save ? 'No save loaded' : !save.playerProfile ? 'Unrecognized original attributes · named edits disabled' : playerDrafts.size ? 'Unapplied player draft' : issues.length ? issues.join(' ') : 'Base values · equipment stays untouched';
  $('player-preview').classList.toggle('warning-text', Boolean(save && (!save.playerProfile || issues.length)));
}

function renderPlayer() {
  $('player-fields').disabled = !save || !save.playerProfile;
  for (const name of Object.keys(PLAYER_FIELDS)) $(`player-${name}`).value = playerDrafts.get(name) ?? (slotSave() ? save.player(name) : '');
  updatePlayerPreview();
}

function bagChanges() {
  const id = integer($('bag-id').value, 0, 0x7ff, 'Item ID');
  const definition = catalog.bagDefinition(id);
  const max = id ? bagStackLimit(definition) : 0;
  const quantity = integer($('bag-quantity').value, id ? 1 : 0, max, 'Quantity');
  const changes = { id, quantity };
  if ($('bag-level').value !== '') changes.level = integer($('bag-level').value, 1, 10, 'Item level');
  return { changes, definition, max };
}

function updateBagPreview() {
  $('bag-name').textContent = 'Invalid item ID';
  $('bag-limit').textContent = 'Definition required';
  $('bag-quantity').min = 0;
  $('bag-quantity').max = 9;
  if (!slotSave()) { $('bag-edit-note').textContent = 'Open a slot save to inspect a slot.'; return; }
  const current = inventorySlot(bagSlot);
  $('bag-offset').textContent = `Slot ${bagSlot + 1}`;
  try {
    const id = integer($('bag-id').value, 0, 0x7ff, 'Item ID');
    $('bag-name').textContent = id ? catalog.name(id) : 'Empty · clears the whole record';
    const max = id ? bagStackLimit(catalog.bagDefinition(id)) : 0;
    $('bag-quantity').min = id ? 1 : 0;
    $('bag-quantity').max = max;
    $('bag-limit').textContent = id ? `Maximum ${max} per slot` : 'Quantity must be 0';
    bagChanges();
    $('bag-edit-note').textContent = !id ? 'Applying removes this item.' : id !== current.id ? 'Replacement clears upgrade metadata; blank level starts at 1.' : $('bag-level').value !== '' ? 'Sets every unit’s level; equipment bonuses are not recalculated.' : current.mixedLevels ? `Mixed levels kept: ${current.levels.join(', ')}.` : 'Existing levels and upgrade metadata are kept.';
    $('bag-edit-note').classList.toggle('warning-text', id !== current.id || !id);
  } catch (error) {
    $('bag-edit-note').textContent = error.message;
    $('bag-edit-note').classList.add('warning-text');
  }
}

function bagDisplayItems() {
  const index = new Map(catalog.browse().map(item => [item.id, item.group]));
  const items = slotSave() ? inventoryItems().map(item => ({ ...item, group: index.get(item.id) || 'other' })) : [];
  if ($('bag-view').value === 'all') return items;
  const ranks = new Map(ITEM_GROUPS.map((group, index) => [group.id, index]));
  return items.filter(item => item.id).sort((a, b) => ranks.get(a.group) - ranks.get(b.group) || a.slot - b.slot);
}

function groupedOptions(select, items, { selected = '', remove = false } = {}) {
  const nodes = [new Option('Choose an item', '')];
  if (remove) nodes.push(new Option('Empty slot / remove item', '0'));
  for (const group of ITEM_GROUPS) {
    const members = items.filter(item => item.group === group.id);
    if (!members.length) continue;
    const element = document.createElement('optgroup');
    element.label = group.label;
    element.append(...members.map(item => new Option(`${item.name} · ${item.id}`, item.id)));
    nodes.push(element);
  }
  select.replaceChildren(...nodes);
  select.value = [...select.options].some(option => option.value === String(selected)) ? String(selected) : '';
}

function renderBagChoices() {
  const group = $('bag-group').value;
  const groups = catalog.groups({ editableOnly: true });
  $('bag-group').replaceChildren(new Option('All groups', 'all'), ...groups.map(entry => new Option(`${entry.label} (${entry.count})`, entry.id)));
  $('bag-group').value = groups.some(entry => entry.id === group) ? group : 'all';
  groupedOptions($('bag-results'), catalog.browse({ query: $('bag-search').value, group: $('bag-group').value, editableOnly: true }), { selected: $('bag-id').value, remove: true });
}

function renderBag() {
  const items = slotSave() ? inventoryItems() : [];
  const definitions = (catalog.count('item') ?? 0) > 0;
  $('allow-bag').disabled = !save || !save.playerProfile || !definitions;
  $('bag-fields').disabled = $('allow-bag').disabled || !$('allow-bag').checked;
  $('bag-source').textContent = !definitions ? 'Load item definitions in Expert tools to enable editing.' : !save?.playerProfile && save ? 'Original player layout needs verification.' : '';
  $('bag-summary').textContent = slotSave() ? `${items.filter(item => item.id).length} occupied / ${INVENTORIES[selectedContainer()].slots} saved slots` : 'No slot save loaded';
  $('container-count').textContent = `${INVENTORIES[selectedContainer()].slots} saved slots`;
  const itemIndex = new Map(catalog.browse().map(item => [item.id, item.group]));
  const slotGroups = [];
  for (const group of [...ITEM_GROUPS, { id: 'empty', label: 'Empty slots' }]) {
    const members = items.filter(item => (item.id ? itemIndex.get(item.id) || 'other' : 'empty') === group.id);
    if (!members.length) continue;
    const element = document.createElement('optgroup');
    element.label = group.label;
    element.append(...members.map(item => new Option(`${item.slot + 1} · ${item.id ? `${catalog.name(item.id)} ×${item.quantity}` : 'Empty'}`, item.slot)));
    slotGroups.push(element);
  }
  $('bag-slot').replaceChildren(...slotGroups);
  $('bag-slot').value = bagSlot;
  $('bag-list').replaceChildren();
  const displayed = bagDisplayItems();
  const pages = Math.max(1, Math.ceil(displayed.length / BAG_PAGE_SIZE));
  bagPage = Math.max(0, Math.min(bagPage, pages - 1));
  let lastGroup;
  for (const item of displayed.slice(bagPage * BAG_PAGE_SIZE, (bagPage + 1) * BAG_PAGE_SIZE)) {
    if ($('bag-view').value === 'occupied' && item.group !== lastGroup) {
      const heading = document.createElement('div');
      heading.className = 'bag-group-heading';
      heading.textContent = ITEM_GROUPS.find(group => group.id === item.group)?.label || 'Other items';
      $('bag-list').append(heading);
      lastGroup = item.group;
    }
    const button = document.createElement('button');
    button.type = 'button';
    const changed = !equalBytes(save.data.subarray(item.offset, item.offset + ITEM_RECORD_SIZE), save.original.subarray(item.offset, item.offset + ITEM_RECORD_SIZE));
    button.className = `bag-slot-button${changed ? ' changed' : ''}`;
    button.setAttribute('aria-pressed', String(item.slot === bagSlot));
    const title = document.createElement('span');
    title.textContent = `${item.slot + 1} · ${item.id ? catalog.name(item.id) : 'Empty'}`;
    const detail = document.createElement('span');
    detail.className = 'small';
    detail.textContent = item.id ? `×${item.quantity} · ${item.mixedLevels ? 'Mixed levels' : `Level ${item.level}`}${changed ? ' · edited' : ''}` : changed ? 'Cleared · edited' : 'Empty record';
    button.append(title, detail);
    button.addEventListener('click', () => selectBagSlot(item.slot));
    $('bag-list').append(button);
  }
  if (slotSave() && !displayed.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'Container is empty. Choose an empty slot below to add an item.';
    $('bag-list').append(empty);
  }
  $('bag-page').textContent = `${bagPage + 1} / ${pages}`;
  $('bag-prev').disabled = !slotSave() || bagPage === 0;
  $('bag-next').disabled = !slotSave() || bagPage >= pages - 1;
  for (const name of ['id', 'quantity', 'level']) $(`bag-${name}`).value = bagDrafts.get(name) ?? (name === 'level' ? '' : slotSave() ? inventorySlot(bagSlot)[name] : '');
  updateBagPreview();
  renderBagChoices();
}

function selectBagSlot(slot) {
  if (bagDrafts.size && slot !== bagSlot) {
    $('bag-slot').value = bagSlot;
    notify('Apply or clear the bag draft before switching slots.', true);
    return;
  }
  bagSlot = slot;
  if (!inventorySlot(slot).id) $('bag-view').value = 'all';
  bagPage = Math.floor(Math.max(0, bagDisplayItems().findIndex(item => item.slot === slot)) / BAG_PAGE_SIZE);
  renderBag();
}

function trackBagDraft(name) {
  const value = $(`bag-${name}`).value;
  const current = inventorySlot(bagSlot);
  if (name === 'level' ? value === '' : value !== '' && Number(value) === current[name]) bagDrafts.delete(name);
  else bagDrafts.set(name, value);
}

function searchItems(query) {
  return catalog.browse({ query });
}

function renderSystem() {
  const system = save?.kind === 'system';
  $('allow-system').disabled = !system;
  $('system-flags').replaceChildren();
  $('system-extra-flags').replaceChildren();
  for (const { bit, label: text } of SYSTEM_FLAGS) {
    const label = document.createElement('label');
    label.className = 'check-label';
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.disabled = !system || !$('allow-system').checked;
    input.checked = system && save.systemFlag(bit) === 1;
    input.addEventListener('change', () => attempt(() => {
      if (!$('allow-system').checked || !system) throw new Error('Enable system editing first.');
      save.setSystemFlags({ [bit]: input.checked ? 1 : 0 });
      render();
      notify('System flag applied. It does not advance a slot’s story or simulate an ending.');
    }));
    label.append(input, `${text} · bit ${bit}`);
    (bit === 4 ? $('system-extra-flags') : $('system-flags')).append(label);
  }
}

function renderProgress() {
  $('story-ack').disabled = !slotSave();
  const enabled = slotSave() && $('allow-flags').checked && $('story-ack').checked;
  $('story-fields').disabled = !enabled;
  $('story-stage').value = storyValueDraft ?? (slotSave() ? save.flag(STORY_REGISTER) : '');
  $('story-current').textContent = slotSave() ? `Current stage ${save.flag(STORY_REGISTER)}${storyValueDraft !== undefined ? ' · draft not applied' : ''}` : 'No slot save loaded';
  $('save-profile').disabled = !slotSave() || demo;
  $('save-profile').firstChild.textContent = profileDraft ? 'Download staged profile' : 'Download profile';
  $('apply-profile').disabled = !enabled || !profileDraft;
  $('profile-preview').replaceChildren();
  $('profile-summary').textContent = !profileDraft ? 'No profile staged' : `${profileDraft.label} · ${profileDraft.entries.length} named values · not applied`;
  for (const { variable, value } of profileDraft?.entries.slice(0, 100) || []) {
    const row = document.createElement('div');
    row.className = 'change-row profile-row';
    const before = slotSave() ? save.flag(variable) : '—';
    const name = document.createElement('code');
    name.textContent = variable.name;
    const values = document.createElement('span');
    values.className = 'small muted';
    values.textContent = `${before} → ${value}`;
    row.append(name, values);
    $('profile-preview').append(row);
  }
  if (profileDraft?.entries.length > 100) {
    const rest = document.createElement('span');
    rest.className = 'small muted';
    rest.textContent = `Preview shows the first 100 of ${profileDraft.entries.length} values; all are applied. Use the exported JSON to review the full profile.`;
    $('profile-preview').append(rest);
  }
}

function renderConversion() {
  const target = $('export-platform').value;
  $('export-platform').disabled = !save;
  for (const option of $('export-platform').options) option.disabled = save ? save.kind === 'system' ? option.value !== 'shared' : option.value === 'shared' : false;
  $('source-platform').textContent = !save ? 'No save loaded' : save.kind === 'system' ? 'System · shared container' : `Source: ${words(save.platform)}`;
  const converting = save && target !== save.platform;
  $('conversion-label').hidden = !converting;
  $('conversion-note').textContent = !save ? 'Export keeps the source format by default.' : save.kind === 'system' ? 'PC and supplied Switch system saves share size, signature and CRC. Platform-specific settings are not remapped.' : converting ? conversionIssue() || 'Experimental: common fields retained, eight candidate padding bytes inserted / removed, 224-byte trailer preserved. Cross-platform loading remains untested.' : `${words(save.platform)} slot · ${save.size.toLocaleString()} bytes · source format preserved`;
}

function renderGender() {
  $('gender-export-card').hidden = !slotSave();
  $('correct-gender').disabled = !slotSave();
  const enabled = slotSave() && $('correct-gender').checked;
  $('gender-export-fields').hidden = !enabled;
  $('export-gender').disabled = !enabled;
  $('reset-appearance').disabled = !enabled;
  if (!slotSave()) { $('gender-preview').textContent = 'No slot save loaded'; return; }
  const label = value => value === 'male' ? 'Male · Lest' : value === 'female' ? 'Female · Frey' : 'Unrecognized';
  try {
    const { gender, resetAppearance } = exportOptions();
    const correction = save.genderCorrection(gender, resetAppearance);
    const appearance = save.appearance();
    const swapped = appearance.swapped || appearance.override !== 0;
    $('gender-preview').textContent = correction ? `Export: ${label(correction.gender)}.${resetAppearance ? ' Appearance, portrait and outfit will be reset to this protagonist.' : swapped ? ' Appearance override is active; enable reset to match the model and portrait too.' : ''}` : `Saved gender: ${label(save.gender())}.${swapped ? ' A separate appearance override is active.' : ''} Original is not overwritten.`;
    $('gender-preview').classList.toggle('warning-text', Boolean(correction && (resetAppearance || swapped)));
  } catch (error) {
    $('gender-preview').textContent = error.message;
    $('gender-preview').classList.add('warning-text');
  }
}

function refreshLayout() {
  const loaded = Boolean(save);
  const system = save?.kind === 'system';
  const visibility = { calendar: slotSave(), player: slotSave() && save.playerProfile, bag: slotSave() && save.playerProfile, system, progress: slotSave(), flags: slotSave(), 'system-expert': system, review: loaded, 'expert-tools': loaded };
  for (const [id, visible] of Object.entries(visibility)) {
    $(id).hidden = !visible;
    const link = document.querySelector(`.nav-link[href="#${id}"]`);
    if (link) link.hidden = !visible;
  }
  for (const link of document.querySelectorAll('[data-expert-link]')) link.hidden = true;
  $('expert-drafts').hidden = !expertDrafts();
}

function render({ syncCalendar = false } = {}) {
  const loaded = Boolean(save);
  refreshLayout();
  $('calendar-fields').disabled = !slotSave();
  $('allow-flags').disabled = !slotSave();
  $('allow-raw').disabled = !loaded;
  $('raw-fields').disabled = !loaded || !$('allow-raw').checked;
  $('inspect-bytes').disabled = !loaded;
  $('undo').disabled = !save?.undoStack.length;
  $('redo').disabled = !save?.redoStack.length;
  $('reset').disabled = !save?.dirty;
  $('download-original').disabled = !loaded || demo;
  $('download-report').disabled = !loaded || demo;
  $('repair-label').hidden = !loaded || save.crcValid;
  $('drop-zone').classList.toggle('loaded', loaded);
  const changed = save?.changedBytes ?? 0;
  $('changes-value').textContent = `${changed.toLocaleString()} ${changed === 1 ? 'byte' : 'bytes'}`;
  $('nav-count').textContent = changed;
  $('nav-count').setAttribute('aria-label', `${changed} changed bytes`);
  $('changes-detail').textContent = save?.dirty ? `${save.undoStack.length} undoable ${save.undoStack.length === 1 ? 'edit' : 'edits'}` : 'Original stays untouched';
  $('document-state').textContent = demo ? 'Demo · export disabled' : !loaded ? 'Open a save to begin' : hasUnexportedEdits() ? 'Unexported changes' : lastExport && equalBytes(save.data, lastExport) ? 'Current edits exported' : 'Original loaded · no edits';
  document.title = `${hasUnexportedEdits() ? '• ' : ''}Rune Factory 4 Special · Save editor`;
  if (loaded) {
    $('platform-badge').textContent = save.kind === 'system' ? 'System save' : words(save.platform);
    $('date-value').previousElementSibling.textContent = slotSave() ? 'In-game date' : 'System state';
    $('drop-heading').textContent = save.name;
    $('drop-description').textContent = demo ? 'Synthetic data · not a playable save' : 'Save loaded · drop another to switch';
    $('file-hint').textContent = `${save.size.toLocaleString()} bytes · ${demo ? 'Demo workspace' : 'Original held in memory'}`;
    $('sidebar-file').textContent = save.name;
    $('sidebar-size').textContent = demo ? 'Synthetic data' : `${(save.size / 1024).toFixed(2)} KiB · ${save.kind === 'system' ? 'System' : words(save.platform)}`;
    $('integrity-value').textContent = save.crcValid ? 'Checksum valid' : 'CRC mismatch';
    $('integrity-value').className = `metric-value ${save.crcValid ? 'accent-text' : 'warning-text'}`;
    $('integrity-detail').textContent = save.crcValid ? 'Original CRC-32 verified' : 'Repair requires consent';
    const season = slotSave() ? SEASONS[save.get('season')] || 'Invalid season' : '';
    $('date-value').textContent = slotSave() ? `${season} ${save.get('day')}` : 'System settings';
    $('date-detail').textContent = slotSave() ? `Year ${save.get('year')}` : `Flags ${hex(save.readNumber(8, 'u32'), 8)}`;
    try { $('export-crc').textContent = hex(save.view(save.build(exportOptions(true))).getUint32(save.crcOffset, true), 8); }
    catch { $('export-crc').textContent = 'Export blocked'; }
    $('export-name').textContent = demo ? 'Demo exports are disabled.' : `Downloads as ${exportFilename()}`;
    const issues = [...save.calendarIssues(), ...(save.playerProfile ? save.playerIssues() : [])];
    $('checksum-label').textContent = issues.length ? 'Fields need correction' : 'Rebuilt on export';
    $('checksum-label').className = `badge ${issues.length ? 'warning' : 'accent'}`;
  }
  if (syncCalendar || !loaded) fillCalendar();
  else updateDatePreview();
  renderFlags();
  renderHex();
  renderChanges();
  renderReference();
  renderTyped();
  renderPlayer();
  renderBag();
  renderSystem();
  renderProgress();
  renderConversion();
  renderGender();
  extraUi.render();
  updateExportButton();
}

function openDocument(next, isDemo = false) {
  const apply = () => {
    save = next;
    demo = isDemo;
    extraUi.clear();
    $('bag-container').value = 'bag';
    lastContainer = 'bag';
    lastExport = undefined;
    flagDrafts.clear();
    playerDrafts.clear();
    bagDrafts.clear();
    storyValueDraft = undefined;
    profileDraft = undefined;
    $('story-ack').checked = false;
    $('allow-system').checked = false;
    $('allow-conversion').checked = false;
    $('correct-gender').checked = false;
    $('export-gender').value = 'original';
    $('reset-appearance').checked = false;
    $('expert-tools').open = false;
    $('export-platform').value = save.platform;
    $('raw-offset').value = save.kind === 'system' ? '0x00008' : '0x00014';
    bagSlot = slotSave() ? save.bagItems().find(item => item.id)?.slot ?? 0 : 0;
    bagPage = 0;
    $('bag-view').value = 'occupied';
    $('bag-group').value = 'all';
    $('allow-bag').checked = false;
    $('bag-search').value = '';
    $('bag-results').replaceChildren(new Option('Search by name or ID', ''));
    flagPage = 0;
    $('allow-flags').checked = false;
    $('allow-raw').checked = false;
    $('repair-crc').checked = false;
    $('raw-value').value = '';
    $('typed-value').value = '';
    $('typed-offset').value = '';
    for (const option of $('season').querySelectorAll('[data-invalid]')) option.remove();
    $('replace-confirm').hidden = true;
    pendingReplacement = undefined;
    render({ syncCalendar: true });
    const issues = save.calendarIssues();
    notify(isDemo ? 'Demo mode. Open your own save when ready.' : !save.crcValid ? 'Original checksum mismatch. Repair will not recover missing or damaged game data.' : issues.length ? `Save loaded. ${issues.join(' ')}` : 'Save loaded. Your original file stays untouched.', !save.crcValid || Boolean(issues.length));
  };
  if (hasUnexportedEdits() || pendingDrafts()) {
    pendingReplacement = apply;
    $('replace-confirm').hidden = false;
    $('cancel-replace').focus();
  } else apply();
}

async function loadFile(file) {
  if (!file || loading) return;
  if (![SAVE_SIZE, SWITCH_SAVE_SIZE, SYSTEM_SAVE_SIZE].includes(file.size)) { notify('Unsupported file size. Choose a PC / Switch slot or rf4_sys.sav.', true); return; }
  loading = true;
  $('open-save').disabled = true;
  try {
    const next = new SaveDocument(await file.arrayBuffer(), file.name);
    openDocument(next);
  } catch (error) { notify(error.message, true); }
  finally { loading = false; $('open-save').disabled = false; }
}

function download(bytes, name, type = 'application/octet-stream') {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

function exportSave() {
  attempt(() => {
    if (!save || demo) throw new Error('Open a real slot or system save before exporting.');
    if (pendingDrafts()) throw new Error('Apply or clear draft fields before exporting.');
    const output = save.build(exportOptions());
    download(output, exportFilename());
    lastExport = save.data.slice();
    render();
    notify('Export download requested. Keep a backup before replacing your game save.');
  });
}

$('open-save').addEventListener('click', () => $('save-input').click());
$('drop-zone').addEventListener('click', () => $('save-input').click());
$('drop-zone').addEventListener('keydown', event => {
  if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); $('save-input').click(); }
});
$('save-input').addEventListener('change', event => { loadFile(event.target.files[0]); event.target.value = ''; });
for (const type of ['dragenter', 'dragover']) $('drop-zone').addEventListener(type, event => { event.preventDefault(); $('drop-zone').classList.add('dragging'); });
$('drop-zone').addEventListener('dragleave', () => $('drop-zone').classList.remove('dragging'));
$('drop-zone').addEventListener('drop', event => {
  event.preventDefault();
  $('drop-zone').classList.remove('dragging');
  if (event.dataTransfer.files.length !== 1) { notify('Choose one slot save at a time.', true); return; }
  loadFile(event.dataTransfer.files[0]);
});
window.addEventListener('dragover', event => event.preventDefault());
window.addEventListener('drop', event => event.preventDefault());
$('load-demo').addEventListener('click', () => openDocument(createDemo(), true));
$('cancel-replace').addEventListener('click', () => { pendingReplacement = undefined; $('replace-confirm').hidden = true; });
$('confirm-replace').addEventListener('click', () => pendingReplacement?.());
$('calendar-form').addEventListener('submit', event => {
  event.preventDefault();
  attempt(() => {
    if (!save) return;
    save.setCalendar({ day: $('day').value, season: $('season').value, year: $('year').value });
    render({ syncCalendar: true });
    notify('Calendar applied. Review your changes before exporting.');
  });
});
for (const name of ['day', 'season', 'year']) $(name).addEventListener('input', updateDatePreview);
$('undo').addEventListener('click', () => { save?.undo(); render({ syncCalendar: true }); notify('Last edit undone.'); });
$('redo').addEventListener('click', () => { save?.redo(); render({ syncCalendar: true }); notify('Last edit redone.'); });
$('reset').addEventListener('click', () => { save?.reset(); extraUi.clear(); $('raw-value').value = ''; $('typed-value').value = ''; flagDrafts.clear(); playerDrafts.clear(); bagDrafts.clear(); storyValueDraft = undefined; profileDraft = undefined; render({ syncCalendar: true }); notify('Original restored in memory. You can undo this.'); });
$('allow-system').addEventListener('change', renderSystem);
$('expert-tools').addEventListener('toggle', () => { refreshLayout(); updateExportButton(); });
document.querySelector('.nav-link[href="#expert-tools"]').addEventListener('click', () => { $('expert-tools').open = true; });
for (const id of ['correct-gender', 'export-gender', 'reset-appearance']) $(id).addEventListener('change', render);
$('story-ack').addEventListener('change', renderProgress);
$('story-stage').addEventListener('input', () => {
  storyValueDraft = slotSave() && $('story-stage').value !== '' && Number($('story-stage').value) === save.flag(STORY_REGISTER) ? undefined : $('story-stage').value;
  updateExportButton();
});
$('story-marker').replaceChildren(new Option('Choose a marker', ''), ...STORY_MARKERS.map(marker => new Option(`${marker.value} · ${marker.label}`, marker.value)));
$('story-marker').addEventListener('change', () => {
  if ($('story-marker').value === '') return;
  $('story-stage').value = $('story-marker').value;
  $('story-stage').dispatchEvent(new Event('input'));
  renderProgress();
});
$('clear-story').addEventListener('click', () => { storyValueDraft = undefined; renderProgress(); updateExportButton(); });
$('story-form').addEventListener('submit', event => {
  event.preventDefault();
  attempt(() => {
    if (!slotSave() || !$('allow-flags').checked || !$('story-ack').checked) throw new Error('Enable story editing and acknowledge incomplete jump dependencies first.');
    save.setFlag(STORY_REGISTER, $('story-stage').value);
    storyValueDraft = undefined;
    flagDrafts.delete(STORY_REGISTER.name);
    render();
    notify('Main-story register applied. This is not a simulated checkpoint; prerequisites and world state were not synthesized.', true);
  });
});
$('load-profile').addEventListener('click', () => $('profile-input').click());
$('profile-input').addEventListener('change', async event => {
  const file = event.target.files[0];
  event.target.value = '';
  if (!file) return;
  try {
    if (profileDraft) throw new Error('Apply or clear the staged profile before reading another.');
    if (file.size > 1024 * 1024) throw new Error('Progress profiles must be smaller than 1 MiB.');
    const next = progressCatalog.parseProfile(await file.text());
    profileDraft = next;
    renderProgress();
    updateExportButton();
    notify('Progress profile staged only. Review its flags before applying.', true);
  } catch (error) { notify(error.message, true); }
});
$('load-progress-donor').addEventListener('click', () => $('progress-donor-input').click());
$('progress-donor-input').addEventListener('change', async event => {
  const file = event.target.files[0];
  event.target.value = '';
  if (!file) return;
  try {
    if (profileDraft) throw new Error('Apply or clear the staged profile before reading another donor.');
    if (![SAVE_SIZE, SWITCH_SAVE_SIZE].includes(file.size)) throw new Error('Donors must be a PC or Switch slot save.');
    const donor = new SaveDocument(await file.arrayBuffer(), file.name);
    if (!donor.crcValid) throw new Error('The donor checksum is invalid. No flags were staged.');
    const flags = progressCatalog.snapshot(donor, $('progress-scope').value);
    profileDraft = { label: `${file.name} · ${$('progress-scope').value}`, entries: progressCatalog.entries(flags) };
    renderProgress();
    updateExportButton();
    notify('Donor flags staged. Inventory, NPC records, location and request records are not copied or initialized.', true);
  } catch (error) { notify(error.message, true); }
});
$('save-profile').addEventListener('click', () => attempt(() => {
  if (!slotSave() || demo) throw new Error('Open a real slot save first.');
  const profile = { format: 'rf4s-progress-v1', label: profileDraft?.label || `${save.name} · ${$('progress-scope').value}`, flags: profileDraft ? Object.fromEntries(profileDraft.entries.map(({ variable, value }) => [variable.name, value])) : progressCatalog.snapshot(save, $('progress-scope').value) };
  download(JSON.stringify(profile, null, 2), `${save.name.replace(/\.sav$/i, '')}.progress.json`, 'application/json');
  notify(profileDraft ? 'Staged profile download requested for full review.' : 'Applied flag snapshot downloaded. Unapplied drafts are not included.');
}));
$('clear-profile').addEventListener('click', () => { profileDraft = undefined; renderProgress(); updateExportButton(); });
$('apply-profile').addEventListener('click', () => attempt(() => {
  if (!slotSave() || !profileDraft || !$('allow-flags').checked || !$('story-ack').checked) throw new Error('Enable story editing and acknowledge incomplete dependencies first.');
  save.setFlags(profileDraft.entries, profileDraft.label);
  profileDraft = undefined;
  flagDrafts.clear();
  render();
  notify('Named flags applied as one undoable edit. This does not replay events, grant rewards or initialize quest records.', true);
}));
$('export-platform').addEventListener('change', () => { $('allow-conversion').checked = false; render(); });
$('allow-conversion').addEventListener('change', render);
$('player-form').addEventListener('submit', event => {
  event.preventDefault();
  attempt(() => {
    if (!save?.playerProfile) throw new Error('Open a save with recognized player attributes first.');
    save.setPlayer(Object.fromEntries(Object.keys(PLAYER_FIELDS).map(name => [name, $(`player-${name}`).value])));
    playerDrafts.clear();
    render();
    notify('Player values applied in memory. Review the byte changes before exporting.');
  });
});
$('clear-player').addEventListener('click', () => { playerDrafts.clear(); renderPlayer(); updateExportButton(); });
$('allow-bag').addEventListener('change', () => {
  if (bagDrafts.size && !$('allow-bag').checked) {
    $('allow-bag').checked = true;
    notify('Apply or clear the bag draft before disabling editing.', true);
  }
  renderBag();
});
$('bag-slot').addEventListener('change', () => selectBagSlot(Number($('bag-slot').value)));
let lastContainer = 'bag';
$('bag-container').addEventListener('change', () => {
  if (bagDrafts.size) { $('bag-container').value = lastContainer; notify('Apply or clear the item draft before changing containers.', true); return; }
  lastContainer = selectedContainer();
  bagSlot = slotSave() ? inventoryItems().find(item => item.id)?.slot ?? 0 : 0;
  bagPage = 0; renderBag();
});
$('bag-view').addEventListener('change', () => { bagPage = 0; renderBag(); });
$('bag-prev').addEventListener('click', () => { bagPage--; renderBag(); });
$('bag-next').addEventListener('click', () => { bagPage++; renderBag(); });
for (const name of ['id', 'quantity', 'level']) $(`bag-${name}`).addEventListener('input', () => {
  if (!save) return;
  trackBagDraft(name);
  if (name === 'id') renderBagChoices();
  updateBagPreview();
  updateExportButton();
});
$('bag-search').addEventListener('input', renderBagChoices);
$('bag-group').addEventListener('change', renderBagChoices);
$('bag-results').addEventListener('change', () => {
  if (!$('bag-results').value || !save) return;
  attempt(() => {
    const id = Number($('bag-results').value);
    if (id) bagStackLimit(catalog.bagDefinition(id));
    $('bag-id').value = id;
    if (id !== inventorySlot(bagSlot).id || !id) { $('bag-quantity').value = id ? 1 : 0; trackBagDraft('quantity'); }
    trackBagDraft('id');
    updateBagPreview();
    updateExportButton();
  });
});
$('clear-bag').addEventListener('click', () => { bagDrafts.clear(); renderBag(); updateExportButton(); });
$('bag-form').addEventListener('submit', event => {
  event.preventDefault();
  attempt(() => {
    if (!$('allow-bag').checked || $('bag-fields').disabled) throw new Error('Enable bag editing and load item definitions first.');
    const { changes, definition } = bagChanges();
    save.setInventoryItem(selectedContainer(), bagSlot, changes, definition);
    bagDrafts.clear();
    render();
    notify(`${INVENTORIES[selectedContainer()].label} slot applied in memory. Replacements reset metadata; same-item edits preserve it.`);
  });
});
$('load-symbols').addEventListener('click', () => $('symbol-input').click());
$('symbol-input').addEventListener('change', async event => {
  const file = event.target.files[0];
  event.target.value = '';
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) { notify('Symbol tables must be smaller than 5 MiB.', true); return; }
  try {
    const parsed = parseEmdeb(await file.arrayBuffer());
    const main = parsed.find(v => v.name === STORY_REGISTER.name);
    if (!main || main.bitOffset !== 0 || main.width !== 9) throw new Error('Unexpected story-register layout. Symbols were not loaded.');
    if (profileDraft || flagDrafts.size) throw new Error('Apply or clear progress drafts before replacing developer symbols.');
    progressCatalog = new ProgressCatalog(parsed);
    symbols = progressCatalog.variables;
    flagPage = 0;
    renderFlags();
    notify(`Loaded ${symbols.length.toLocaleString()} developer symbols. Story changes remain opt-in.`);
  } catch (error) { notify(error.message, true); }
});
$('allow-flags').addEventListener('change', () => { if (!$('allow-flags').checked) flagDrafts.clear(); renderFlags(); renderProgress(); updateExportButton(); });
for (const id of ['flag-search', 'flag-filter', 'flag-group']) $(id).addEventListener(id === 'flag-search' ? 'input' : 'change', () => { flagPage = 0; renderFlags(); });
$('flag-prev').addEventListener('click', () => { flagPage--; renderFlags(); });
$('flag-next').addEventListener('click', () => { flagPage++; renderFlags(); });
$('allow-raw').addEventListener('change', () => {
  $('raw-fields').disabled = !save || !$('allow-raw').checked;
  renderTyped();
  renderReference();
  updateExportButton();
  if ($('allow-raw').checked) notify('Raw edits are unverified. Use only offsets you have independently confirmed.', true);
});
$('raw-value').addEventListener('input', updateExportButton);
$('raw-form').addEventListener('submit', event => {
  event.preventDefault();
  attempt(() => {
    if (!save || !$('allow-raw').checked) throw new Error('Enable raw byte editing first.');
    save.patchBytes($('raw-offset').value, $('raw-value').value);
    $('raw-value').value = '';
    render({ syncCalendar: true });
    notify('Raw bytes applied. Check the exact byte changes before export.', true);
  });
});
$('inspect-bytes').addEventListener('click', renderHex);
$('typed-value').addEventListener('input', updateExportButton);
for (const id of ['typed-offset', 'typed-type', 'typed-meaning']) $(id).addEventListener(id === 'typed-offset' ? 'input' : 'change', renderTyped);
$('clear-typed').addEventListener('click', () => { $('typed-value').value = ''; updateExportButton(); });
$('typed-form').addEventListener('submit', event => {
  event.preventDefault();
  attempt(() => {
    if (!save || !$('allow-raw').checked) throw new Error('Enable raw byte editing first.');
    let value = semanticValue($('typed-value').value, $('typed-meaning').value);
    if ($('typed-meaning').value === 'item') value = catalog.validateItem(value);
    save.setNumber($('typed-offset').value, $('typed-type').value, value);
    $('raw-offset').value = $('typed-offset').value;
    $('typed-value').value = '';
    render({ syncCalendar: true });
    notify('Save value applied at your manual offset. Review the exact byte changes.', true);
  });
});
$('reference-table').addEventListener('change', referenceFields);
$('reference-field').addEventListener('change', renderReference);
$('reference-item-id').addEventListener('input', renderReference);
$('item-search').addEventListener('input', () => {
  const matches = searchItems($('item-search').value.trim());
  groupedOptions($('item-results'), matches);
});
$('item-results').addEventListener('change', () => { if ($('item-results').value) { $('reference-item-id').value = $('item-results').value; renderReference(); } });
$('use-reference-id').addEventListener('click', () => attempt(() => {
  if (!save || !$('allow-raw').checked) throw new Error('Enable raw byte editing first.');
  const id = catalog.validateItem($('reference-item-id').value);
  $('typed-type').value = 'u16';
  $('typed-meaning').value = 'item';
  $('typed-value').value = String(id);
  renderTyped();
  updateExportButton();
  $('typed-offset').focus();
  notify('Item ID copied to a draft. Enter a verified save offset; nothing was written.');
}));
$('read-item-tables').addEventListener('click', () => $('item-table-input').click());
$('item-table-input').addEventListener('change', async event => {
  const files = [...event.target.files];
  event.target.value = '';
  if (!files.length) return;
  try {
    if (files.length > 4 || files.some(file => file.size > 16 * 1024 * 1024)) throw new Error('Read at most four reference tables, each smaller than 16 MiB.');
    const tables = await Promise.all(files.map(async file => new ItemTable(await file.arrayBuffer(), detectItemTable(file.name))));
    for (const table of tables) catalog.add(table);
    renderReference();
    renderBag();
    notify('Reference tables read locally. Your save and game files were not changed.');
  } catch (error) { notify(error.message, true); }
});
$('repair-crc').addEventListener('change', updateExportButton);
$('export-save').addEventListener('click', exportSave);
$('download-original').addEventListener('click', () => {
  if (!save || demo) return;
  download(save.original, save.name.replace(/\.sav$/i, '') + '.original.sav');
  notify('Original backup download requested, byte for byte.');
});
$('download-report').addEventListener('click', () => {
  if (!save || demo) return;
  let output;
  try { output = save.build(exportOptions(true)); } catch {}
  const report = {
    application: 'RF4S save editor',
    source: 'arryndoestech/rf4-modkit@799828a433d0e5be537b977918d5a7c773ad1200',
    filename: save.name,
    bytes: save.size,
    kind: save.kind,
    sourcePlatform: save.platform,
    targetPlatform: $('export-platform').value,
    outputBytes: output?.length ?? null,
    conversionExperimental: $('export-platform').value !== save.platform,
    conversionNote: 'Only container conversion and common field layouts checked. In-game acceptance untested.',
    genderCorrection: slotSave() ? { mode: exportOptions().gender, resetAppearance: exportOptions().resetAppearance, original: save.gender(save.original), edited: save.gender(), exported: output ? save.gender(output) : null, originalAppearance: save.appearance(save.original), editedAppearance: save.appearance(), exportedAppearance: output ? save.appearance(output) : null } : null,
    originalChecksumValid: save.crcValid,
    originalChecksum: hex(save.originalCrc, 8),
    exportChecksum: output ? hex(save.view(output).getUint32(save.crcOffset, true), 8) : null,
    calendar: slotSave() ? Object.fromEntries(['day', 'season', 'year'].map(name => [name, { original: save.get(name, save.original), edited: save.get(name) }])) : null,
    player: slotSave() ? Object.fromEntries(Object.keys(PLAYER_FIELDS).map(name => [name, { original: save.player(name, save.original), edited: save.player(name) }])) : null,
    bag: slotSave() ? save.bagItems().filter(item => !equalBytes(save.data.subarray(item.offset, item.offset + ITEM_RECORD_SIZE), save.original.subarray(item.offset, item.offset + ITEM_RECORD_SIZE))).map(item => ({ slot: item.slot + 1, original: save.bagSlot(item.slot, save.original), edited: item })) : null,
    inventories: slotSave() ? Object.fromEntries(Object.keys(INVENTORIES).map(container => [container, save.inventoryItems(container).filter(item => !equalBytes(save.data.subarray(item.offset, item.offset + ITEM_RECORD_SIZE), save.original.subarray(item.offset, item.offset + ITEM_RECORD_SIZE))).map(item => ({ slot: item.slot + 1, original: save.inventorySlot(container, item.slot, save.original), edited: item }))])) : null,
    progress: slotSave() ? progressCatalog.variables.filter(variable => save.flag(variable) !== save.flag(variable, save.original)).map(variable => ({ name: variable.name, original: save.flag(variable, save.original), edited: save.flag(variable) })) : null,
    changedBytes: save.changedBytes,
    changesScope: 'Working save payload only. Export-only gender/appearance overrides are recorded separately; CRC is rebuilt on export.',
    changes: save.changes().map(range => ({ offset: hex(range.offset), before: bytesText(range.before), after: bytesText(range.after) })),
  };
  download(JSON.stringify(report, null, 2), save.name.replace(/\.sav$/i, '') + '.changes.json', 'application/json');
  notify('Change report download requested.');
});

function applyTheme(value) {
  if (value === 'system') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = value;
  $('theme-icon').className = `ti ti-${value === 'light' ? 'sun' : value === 'dark' ? 'moon' : 'device-desktop'}`;
}
try {
  const stored = localStorage.getItem('rf4s-theme');
  if (['light', 'dark', 'system'].includes(stored)) $('theme').value = stored;
} catch {}
applyTheme($('theme').value);
$('theme').addEventListener('change', () => {
  applyTheme($('theme').value);
  try { localStorage.setItem('rf4s-theme', $('theme').value); } catch {}
});

const navLinks = [...document.querySelectorAll('.nav-link')];
for (const link of navLinks) link.addEventListener('click', () => {
  for (const item of navLinks) { item.classList.toggle('active', item === link); if (item === link) item.setAttribute('aria-current', 'location'); else item.removeAttribute('aria-current'); }
});
const observer = new IntersectionObserver(entries => {
  const visible = entries.filter(entry => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
  if (!visible.length) return;
  const id = `#${visible[0].target.id}`;
  for (const link of navLinks) {
    const active = link.getAttribute('href') === id;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
  }
}, { rootMargin: '-5% 0px -60% 0px', threshold: 0 });
for (const section of document.querySelectorAll('main>section, main>details')) observer.observe(section);
window.addEventListener('beforeunload', event => {
  if (hasUnexportedEdits() || pendingDrafts()) { event.preventDefault(); event.returnValue = ''; }
});
window.addEventListener('keydown', event => {
  if (!(event.ctrlKey || event.metaKey)) return;
  const key = event.key.toLowerCase();
  if (key === 's') { event.preventDefault(); exportSave(); }
  if (key === 'o') { event.preventDefault(); $('save-input').click(); }
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName)) return;
  if (key === 'z' || key === 'y') {
    event.preventDefault();
    if (event.shiftKey || key === 'y') save?.redo(); else save?.undo();
    render({ syncCalendar: true });
  }
});
setupPlayer();
referenceFields();
render();

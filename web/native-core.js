// Save operations for the native Qt Widgets app. No DOM, HTML or browser APIs.
import { SaveDocument, createDemo, PLAYER_FIELDS, INVENTORIES, SYSTEM_FLAGS, SEASONS, STORY_REGISTER, parseEmdeb, bagStackLimit } from './save-core.js';
import { ExtendedSave, SKILLS, PEOPLE_NAMES, STAT_FIELDS, TROPHIES } from './extended-core.js';
import { ItemCatalog, ItemTable, detectItemTable } from './game-reference.js';
import { SaveReferences, parseRecipes, RECIPE_FILES } from './save-reference.js';
import { MarriageEditor, MARRIAGE_CANDIDATES, MARRIAGE_FIELDS } from './marriage-core.js';
import { itemDetails, editInventoryItem, equipmentItem, equipmentElement, ELEMENTS } from './item-details.js';
import { ProgressCatalog } from './progress-core.js';
import { SAVE_METADATA } from './save-metadata.js';

let save = null;
let catalog = new ItemCatalog();
let recipes = new SaveReferences();
let progress = new ProgressCatalog(SAVE_METADATA.symbols, SAVE_METADATA.ctFlags);
const requireSave = () => { if (!save) throw new Error('Open a save first.'); return save; };
const extra = () => new ExtendedSave(requireSave());
const marriage = () => new MarriageEditor(requireSave(), progress.variables);

export function nativeInvoke(operation, args = {}) {
  switch (operation) {
    case 'constants': return { player: PLAYER_FIELDS, inventories: INVENTORIES, systemFlags: SYSTEM_FLAGS, seasons: SEASONS, skills: SKILLS, people: PEOPLE_NAMES, stats: STAT_FIELDS, trophies: TROPHIES, candidates: MARRIAGE_CANDIDATES, marriage: MARRIAGE_FIELDS, elements: ELEMENTS, recipeGroups: RECIPE_FILES };
    case 'open': save = new SaveDocument(args.bytes, args.name); return nativeInvoke('state');
    case 'demoBytes': return Array.from(createDemo().original);
    case 'state': return !save ? null : { name: save.name, kind: save.kind, platform: save.platform, size: save.size, crcValid: save.crcValid, dirty: save.dirty, changedBytes: save.changedBytes, undo: save.undoStack.length, redo: save.redoStack.length, playerProfile: save.playerProfile, calendar: save.kind === 'slot' ? { day: save.get('day'), season: save.get('season'), year: save.get('year') } : null, gender: save.kind === 'slot' ? save.gender() : null };
    case 'references': {
      const nextCatalog = new ItemCatalog(args.items);
      const nextRecipes = new SaveReferences(args.recipes);
      catalog = nextCatalog; recipes = nextRecipes; return true;
    }
    case 'importItems': {
      const tables = args.files.map(file => new ItemTable(file.bytes, detectItemTable(file.name)));
      tables.forEach(table => catalog.add(table)); return true;
    }
    case 'importRecipes': {
      const next = new SaveReferences(); next.tables = new Map(recipes.tables);
      args.files.forEach(file => next.add(parseRecipes(file.bytes, file.name)));
      recipes = next; return true;
    }
    case 'items': return catalog.browse({ editableOnly: args.editableOnly || false });
    case 'definition': {
      const definition = catalog.bagDefinition(args.id);
      return { definition, stack: args.id ? bagStackLimit(definition) : 0, equipment: equipmentItem(definition) };
    }
    case 'inventory': return requireSave().inventoryItems(args.container);
    case 'item': {
      const item = requireSave().inventorySlot(args.container, args.slot);
      let definition = null; let element = null;
      try { definition = catalog.bagDefinition(item.id); } catch {}
      const details = itemDetails(save, args.container, args.slot);
      try { element = equipmentElement(item.id, details, catalog); } catch {}
      return { ...item, details, equipment: equipmentItem(definition), element, stack: definition ? bagStackLimit(definition) : null };
    }
    case 'setItem': return editInventoryItem(requireSave(), args.container, args.slot, args.changes, catalog.bagDefinition(args.changes.id), catalog, args.details || {});
    case 'player': return Object.fromEntries(Object.keys(PLAYER_FIELDS).map(key => [key, requireSave().player(key)]));
    case 'setPlayer': return requireSave().setPlayer(args.changes);
    case 'setCalendar': return requireSave().setCalendar(args.changes);
    case 'marriage': return { ...marriage().values(), ...marriage().events(args.candidate) };
    case 'setMarriage': return marriage().apply(args.changes, args.candidate);
    case 'skills': return SKILLS.map(skill => extra().skill(skill.id));
    case 'setSkill': return extra().setSkill(args.id, args.changes);
    case 'friendship': return Array.from({ length: 25 }, (_, i) => extra().friendship(i + 1));
    case 'setFriendship': return extra().setFriendship(args.id, args.level);
    case 'stats': return extra().stats(args.kind, args.id);
    case 'setStats': return extra().setStats(args.kind, args.id, args.changes);
    case 'monsters': return extra().monsters().filter(monster => monster.occupied);
    case 'setMonster': return extra().setMonster(args.id, args.changes);
    case 'recipes': return recipes.recipes().map(recipe => ({ ...recipe, known: extra().recipe(recipe) }));
    case 'setRecipes': return extra().setRecipes(args.recipes, args.known);
    case 'trophies': return TROPHIES.map(trophy => ({ ...trophy, value: extra().trophy(trophy.name) }));
    case 'setTrophy': return extra().setTrophy(args.name, args.value);
    case 'system': return SYSTEM_FLAGS.map(field => ({ ...field, value: requireSave().systemFlag(field.bit) }));
    case 'setSystem': return requireSave().setSystemFlags(args.changes);
    case 'flags': return progress.variables.map(field => ({ ...field, value: requireSave().flag(field) }));
    case 'setFlag': return requireSave().setFlag(progress.byName.get(args.name), args.value);
    case 'importSymbols': {
      const next = new ProgressCatalog(parseEmdeb(args.bytes));
      const editor = new MarriageEditor(save, next.variables);
      MARRIAGE_FIELDS.forEach(field => editor.field(field.name));
      MARRIAGE_CANDIDATES.forEach(person => editor.eventFields(person.id));
      progress = next; return true;
    }
    case 'profile': return { format: 'rf4s-progress-v1', label: args.label || save.name, flags: progress.snapshot(requireSave(), args.scope || 'all') };
    case 'applyProfile': {
      const profile = progress.parseProfile(args.text);
      return requireSave().setFlags(profile.entries, profile.label);
    }
    case 'reference': return Object.fromEntries(['item', 'equipment', 'upgrade', 'use'].map(type => {
      try { return [type, catalog.record(type, args.id)]; } catch { return [type, null]; }
    }));
    case 'readNumber': return requireSave().readNumber(args.offset, args.type);
    case 'setNumber': return requireSave().setNumber(args.offset, args.type, args.value);
    case 'patchBytes': return requireSave().patchBytes(args.offset, args.text);
    case 'undo': return requireSave().undo();
    case 'redo': return requireSave().redo();
    case 'reset': return requireSave().reset();
    case 'original': return Array.from(requireSave().original);
    case 'working': return Array.from(requireSave().data);
    case 'build': return Array.from(requireSave().build(args));
    case 'changes': return requireSave().changes();
    default: throw new Error('Unknown native save operation.');
  }
}

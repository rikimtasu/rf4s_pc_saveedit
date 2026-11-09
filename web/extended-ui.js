import { ExtendedSave, SKILLS, PEOPLE_NAMES, STAT_FIELDS, TROPHIES } from './extended-core.js';
import { parseRecipes, RECIPE_FILES } from './save-reference.js';

const $ = id => document.getElementById(id);
export const EXTENDED_SECTIONS = ['skills', 'recipes', 'friendship', 'people', 'monsters', 'trophies'];

export class ExtendedUI {
  constructor({ getSave, references, itemName, personName = (_id, name) => name, skillName = (_id, name) => name, changed, draftChanged, notify }) {
    Object.assign(this, { getSave, references, itemName, personName, skillName, changed, draftChanged, notify });
    this.drafts = new Map(EXTENDED_SECTIONS.map(id => [id, new Map()]));
    this.selected = { skills: '0', friendship: '1', people: '1', monsters: '', trophies: TROPHIES[0].name, recipes: '' };
    this.recipeGroup = 'all';
    this.recipeSearch = '';
    this.inputs = new Map(EXTENDED_SECTIONS.map(id => [id, new Map()]));
    const fields = { skills: [['skill-level', 'level'], ['skill-xp', 'xp']], friendship: [['friend-level', 'level']], recipes: [['recipe-known', 'known']], monsters: [['monster-friendship', 'friendship']], trophies: [['trophy-value', 'value']] };
    for (const section of ['people', 'monsters']) {
      const target = section === 'people' ? $('people-stats') : $('monster-stats');
      for (const [key, spec] of Object.entries(STAT_FIELDS)) {
        const label = document.createElement('label');
        const input = document.createElement('input');
        input.id = `${section}-${key}`;
        input.type = 'number'; input.min = spec.min; input.max = spec.max; input.step = 1; input.required = true;
        label.append(spec.label, input); target.append(label);
        this.bindInput(section, input.id, key);
      }
    }
    for (const [section, entries] of Object.entries(fields)) for (const [id, key] of entries) this.bindInput(section, id, key);
    const selectors = { skills: 'skill-id', friendship: 'friend-person', people: 'person-id', monsters: 'monster-id', recipes: 'recipe-id', trophies: 'trophy-id' };
    for (const section of EXTENDED_SECTIONS) {
      $(selectors[section]).addEventListener('change', event => {
        if (this.drafts.get(section).size) { event.target.value = this.selected[section]; this.notify('Apply or clear this draft before switching entries.', true); return; }
        this.selected[section] = event.target.value; this.render();
      });
      $(`allow-${section}`).addEventListener('change', () => { this.render(); this.draftChanged(); });
      $(`clear-${section}`).addEventListener('click', () => { this.drafts.get(section).clear(); this.render(); this.draftChanged(); });
      $(`${section}-form`).addEventListener('submit', event => {
        event.preventDefault();
        this.attempt(() => {
          if (!this.enabled(section)) throw new Error('Enable this editor first.');
          const changes = Object.fromEntries(this.drafts.get(section));
          if (!Object.keys(changes).length) return;
          const editor = this.editor();
          const id = this.selected[section];
          if (section === 'skills') editor.setSkill(id, changes);
          else if (section === 'friendship') editor.setFriendship(id, changes.level);
          else if (section === 'people') editor.setStats('person', id, changes);
          else if (section === 'monsters') {
            const { friendship, ...stats } = changes;
            editor.setMonster(id, { friendship, stats });
          } else if (section === 'trophies') editor.setTrophy(id, changes.value);
          else editor.setRecipes([this.recipe()], changes.known === 'true');
          this.drafts.get(section).clear(); this.changed(`${section} changes applied in memory.`);
        });
      });
      document.querySelector(`.nav-link[href="#${section}"]`).addEventListener('click', () => { $(section).querySelector('details').open = true; });
    }
    for (const id of ['recipe-group', 'recipe-search']) $(id).addEventListener(id === 'recipe-search' ? 'input' : 'change', event => {
      if (this.drafts.get('recipes').size) { event.target.value = id === 'recipe-group' ? this.recipeGroup : this.recipeSearch; this.notify('Apply or clear the recipe draft before filtering.', true); return; }
      this.recipeGroup = $('recipe-group').value; this.recipeSearch = $('recipe-search').value; this.selected.recipes = ''; this.render();
    });
    $('load-recipes').addEventListener('click', () => $('recipe-input').click());
    $('recipe-input').addEventListener('change', async event => {
      const files = [...event.target.files]; event.target.value = '';
      try {
        if (this.drafts.get('recipes').size) throw new Error('Apply or clear recipe drafts before replacing definitions.');
        if (files.length > 21 || files.some(file => file.size > 1024 * 1024)) throw new Error('Read up to 21 recipe tables, each smaller than 1 MiB.');
        const tables = await Promise.all(files.map(async file => parseRecipes(await file.arrayBuffer(), file.name)));
        const staged = Object.create(this.references); staged.tables = new Map(this.references.tables);
        for (const table of tables) staged.add(table);
        this.references.tables = staged.tables; this.selected.recipes = ''; this.render();
        this.notify('Recipe definitions read locally. No game files changed.');
      } catch (error) { this.notify(error.message, true); }
    });
    for (const [id, known] of [['learn-recipe-group', true], ['forget-recipe-group', false]]) $(id).addEventListener('click', () => this.attempt(() => {
      if (!this.enabled('recipes') || this.drafts.get('recipes').size) throw new Error('Enable recipe editing and apply / clear its draft first.');
      const unique = [...new Map(this.filteredRecipes().map(recipe => [recipe.bitOffset, recipe])).values()];
      this.editor().setRecipes(unique, known); this.changed(`${known ? 'Learned' : 'Forgot'} ${unique.length} recipe flags in memory.`);
    }));
  }
  attempt(action) { try { action(); } catch (error) { this.notify(error.message, true); } }
  slot() { return this.getSave()?.kind === 'slot'; }
  editor() { return new ExtendedSave(this.getSave()); }
  pending() { return [...this.drafts.values()].some(draft => draft.size); }
  clear() {
    for (const draft of this.drafts.values()) draft.clear();
    for (const section of EXTENDED_SECTIONS) $(`allow-${section}`).checked = false;
    this.selected.monsters = ''; this.selected.recipes = '';
  }
  enabled(section) { return this.slot() && $(`allow-${section}`).checked && (section !== 'recipes' || this.references.recipes().length > 0) && (section !== 'monsters' || this.selected.monsters !== ''); }
  filteredRecipes() {
    const query = this.recipeSearch.toLowerCase().trim();
    return this.references.recipes(this.recipeGroup).filter(recipe => !query || `${recipe.result} ${this.itemName(recipe.result)}`.toLowerCase().includes(query));
  }
  recipe() { return this.references.recipes().find(recipe => `${recipe.kind}:${recipe.index}` === this.selected.recipes); }
  current(section) {
    if (!this.slot()) return {};
    const editor = this.editor(); const id = this.selected[section];
    if (section === 'skills') return editor.skill(id);
    if (section === 'friendship') return editor.friendship(id);
    if (section === 'people') return editor.stats('person', id);
    if (section === 'monsters') return id === '' ? {} : { ...editor.stats('monster', id), friendship: editor.monster(id).friendship };
    if (section === 'trophies') return { value: editor.trophy(id) };
    return { known: this.recipe() ? editor.recipe(this.recipe()) : false };
  }
  bindInput(section, id, key) {
    const input = $(id); this.inputs.get(section).set(key, input);
    input.addEventListener(input.type === 'checkbox' || input.tagName === 'SELECT' ? 'change' : 'input', () => {
      const value = input.type === 'checkbox' ? String(input.checked) : input.value;
      if (value !== '' && value === String(this.current(section)[key])) this.drafts.get(section).delete(key);
      else this.drafts.get(section).set(key, value);
      this.renderNote(section); this.draftChanged();
    });
  }
  renderNote(section) {
    const notes = { skills: 'Direct levels do not award stat gains; unchanged XP is preserved.', recipes: 'Variants sharing a learned flag change together.', friendship: 'Does not trigger dating, marriage, story or achievements.', people: 'Stored base stats only; derived bonuses are not recalculated.', monsters: 'Existing monsters only; species, barn and chores stay unchanged.', trophies: 'Recorded results only; does not unlock Steam achievements.' };
    $(`${section}-note`).textContent = this.drafts.get(section).size ? 'Draft pending · apply or clear before export' : notes[section];
  }
  options(section, id, options) {
    const select = $(id); select.replaceChildren(...options);
    if (!options.some(option => option.value === this.selected[section])) this.selected[section] = options[0]?.value ?? '';
    select.value = this.selected[section];
  }
  render() {
    const skillOptions = [];
    for (const group of [...new Set(SKILLS.map(skill => skill.group))]) {
      const node = document.createElement('optgroup'); node.label = group;
      node.append(...SKILLS.filter(skill => skill.group === group).map(skill => new Option(this.skillName(skill.id, skill.name), skill.id)));
      skillOptions.push(node);
    }
    $('skill-id').replaceChildren(...skillOptions); $('skill-id').value = this.selected.skills;
    this.options('friendship', 'friend-person', PEOPLE_NAMES.slice(1, 26).map((name, i) => new Option(i + 1 >= 22 && i + 1 <= 23 ? name : this.personName(i + 1, name), i + 1)));
    this.options('people', 'person-id', PEOPLE_NAMES.slice(1).map((name, i) => new Option(i + 1 >= 22 && i + 1 <= 23 ? name : this.personName(i + 1, name), i + 1)));
    const monsters = this.slot() ? this.editor().monsters().filter(monster => monster.occupied) : [];
    this.options('monsters', 'monster-id', monsters.map(monster => new Option(`${monster.id + 1} · ${monster.name || 'Unnamed'} · species ${monster.species}`, monster.id)));
    this.options('trophies', 'trophy-id', TROPHIES.map(trophy => new Option(trophy.label, trophy.name)));
    const trophy = TROPHIES.find(trophy => trophy.name === this.selected.trophies);
    $('trophy-value').replaceChildren(...(trophy.width === 1 ? ['Not recorded', 'Recorded / owned'] : ['None', 'Gold / first', 'Silver / second', 'Bronze / third']).map((label, value) => new Option(label, value)));
    const groups = [...this.references.tables.keys()];
    $('recipe-group').replaceChildren(new Option('All groups', 'all'), ...groups.map(kind => new Option(RECIPE_FILES[kind], kind)));
    $('recipe-group').value = this.recipeGroup;
    const recipes = this.filteredRecipes();
    this.options('recipes', 'recipe-id', recipes.map(recipe => new Option(`${this.itemName(recipe.result)} · difficulty ${recipe.level} · variant ${recipe.index}`, `${recipe.kind}:${recipe.index}`)));
    const recipe = this.recipe();
    $('recipe-count').textContent = this.references.recipes().length ? `${this.references.recipes().length} recipe variants · read-only definitions` : 'Read recipe tables to enable learned-state editing.';
    $('recipe-difficulty').textContent = recipe ? `Recommended difficulty ${recipe.level} is not save-editable. Edit the matching crafting skill above.` : '';
    $('recipe-known').disabled = !recipe;
    $('recipes-form').querySelector('button[type="submit"]').disabled = !recipe;
    for (const section of EXTENDED_SECTIONS) {
      $(section).hidden = !this.slot();
      document.querySelector(`.nav-link[href="#${section}"]`).hidden = !this.slot();
      $(`allow-${section}`).disabled = !this.slot();
      $(`${section}-fields`).disabled = !this.enabled(section);
      const current = this.current(section);
      for (const [key, input] of this.inputs.get(section)) {
        const value = this.drafts.get(section).get(key) ?? current[key] ?? '';
        if (input.type === 'checkbox') input.checked = String(value) === 'true'; else input.value = String(value);
      }
      this.renderNote(section);
    }
    $('skill-level').max = SKILLS[Number(this.selected.skills)].max;
    if (this.slot() && !this.drafts.get('friendship').size) $('friendship-note').textContent += ` Stored points: ${this.editor().friendship(this.selected.friendship).points}.`;
    if (!monsters.length && this.slot()) $('monsters-note').textContent = 'No occupied tamed-monster records. New monster creation is not supported.';
  }
}

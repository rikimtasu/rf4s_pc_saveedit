"""Offline English / Simplified Chinese UI catalog; never translates save data.

Re-translation updates captions only, without recreating controls or losing drafts.
Developer symbols, item IDs, file paths and raw reference JSON remain unchanged.
"""
import re

ZH = {
    'Extra orders': '额外指令', 'Equipment shortcuts': '装备快捷操作',
    'Enemy level increase (0–10)': '敌人等级提升（0–10）',
    'Disable combat EXP': '禁用战斗经验', 'Disable skill EXP': '禁用技能经验',
    'Disable town events': '禁用城镇事件', 'Show enemy levels': '显示敌人等级', 'Show enemy HP': '显示敌人 HP',
    'Appearance order (reload required)': '外观变更指令（需重新加载）',
    'Default main character': '主角默认外观',
    'Opposite-gender appearance (dialogue unchanged)': '异性主角外观（对话性别不变）',
    'Saved order effects only; no point costs or events are executed. To unlock the Extra Orders menu, open rf4_sys.sav and use System save unlocks. Appearance changes do not change dialogue gender. Back up and test in-game.': '仅修改已保存的指令效果，不扣点数或执行事件。解锁额外指令菜单请打开 rf4_sys.sav 并使用“系统存档解锁”。外观变更不改变对话性别。请先备份并在游戏中测试。',
    'Prepare extra-orders unlock': '准备解锁额外指令',
    'Open rf4_sys.sav to unlock Extra Orders.': '请打开 rf4_sys.sav 解锁额外指令。',
    'Unknown extra order field.': '未知的额外指令字段。', 'Choose a supported appearance order.': '请选择支持的外观变更指令。',
    'Prepare maximum soil stats (raw)': '准备最大土壤属性（原始值）',
    'Balanced optimized staff gear': '均衡优化法杖装备', 'Maximum-damage optimized staff gear': '最大伤害优化法杖装备',
    'Give balanced staff gear': '给予均衡法杖装备', 'Give maximum-damage staff gear': '给予最大伤害法杖装备',
    'Crafting attachments': '制作附加材料', 'Upgrades in order': '按顺序强化',
    'Staff': '法杖', 'Shield': '盾牌', 'Armor': '防具', 'Headgear': '头饰', 'Shoes': '鞋', 'Accessory': '饰品',
    'Curated endgame staff sets for Lest or Frey, not a mathematical best-build guarantee. Adds six level-10 items to empty slots in the first 15 bag slots; equip them in-game. Existing items, worn gear and bag capacity are preserved. All saved level/rarity bonuses are maximized. Export to save.': '为雷斯特或芙蕾精选的终盘法杖套装，不保证数学意义的最优搭配。在背包前 15 格中的空格加入六件 10 级装备；请在游戏中穿戴。不覆盖已有物品或已穿装备，也不扩容。已保存的总等级／稀有度加成设为最大。导出后生效。',
    'Damage preset: Strange Pendant ignores enemy DEF/M.DEF AND your own DEF/M.DEF. It sacrifices protection. Final stats, inheritance and staff charge attacks are not simulated; test exported copies in-game.': '伤害预设：奇妙吊坠忽略敌人及玩家自身的 DEF／M.DEF，以牺牲防护换取伤害。不模拟最终属性、继承及法杖蓄力攻击；请在游戏中测试导出副本。',
    'Inspired by the supplied GameFAQs build. For its claimed resistance/INT targets, use level-10 Gold Juice and high resistance skills in-game. Neither buff nor skills are changed here. Positive cloth bonuses are not inverted; the preview shows the actual saved build.': '参考提供的 GameFAQs 搭配。达到帖子所述抗性／智力目标需在游戏中使用 10 级黄金果汁及高抗性技能。本工具不修改增益或技能，不反转布料的正抗性；预览显示实际写入搭配。',
    'I understand experimental gear and the damage preset defense tradeoff': '我理解实验装备风险及伤害预设牺牲防御的代价',
    'Acknowledge experimental gear presets first.': '请先确认实验装备预设风险。',
    'Gear presets require matching item, equipment and upgrade tables.': '装备预设需要匹配的物品、装备及强化数据表。',
    'Free six slots in the first 15 bag slots before giving gear. Existing items are never overwritten.': '给予装备前请腾出背包前 15 格中的六格。不会覆盖已有物品。',
    'Six gear items added in memory. Equip them in-game after exporting.': '六件装备已加入内存。导出后请在游戏中穿戴。',
    'Tourists': '游客人数',
    'Reload game references (optional)': '重新读取游戏数据（可选）',
    'Save as…': '另存为…',
    'Target save file': '目标存档文件',
    'Choose target save slot': '选择目标存档槽位',
    'Choose a target save slot first.': '请先选择目标存档槽位。',
    'Choose a target filename matching the save type.': '请选择与存档类型相符的目标文件。',
    'Use PC output for the PC save folder, or choose Save as for Switch.': '写入 PC 存档目录请使用 PC 格式；Switch 格式请使用另存为。',
    'Save pending edits to the game folder and create a backup.': '将待应用修改保存到游戏存档目录，并先创建备份。',
    'Pending edits are applied automatically when exporting.': '导出时自动应用待保存的修改。',
    'Pending edit · saved on export': '待保存修改 · 导出时自动应用',
    'Saved: ': '已保存：', ' · Backup: ': ' · 备份：',
    'Interface: ': '界面：', 'Game names: ': '游戏名称：',
    'Follow system': '跟随系统',
    'Yes': '是', '&Yes': '是(&Y)', 'No': '否', '&No': '否(&N)',
    'Cancel': '取消', 'Discard': '放弃', 'Open': '打开', 'Save': '保存', 'Close': '关闭',
    '&Open': '打开(&O)', '&Save': '保存(&S)', 'File name:': '文件名：',
    'Files of type:': '文件类型：', 'Look in:': '查找范围：', 'Save in:': '保存位置：',
    'Rune Factory 4 Special · Native save editor': '符文工房 4 豪华版 · 存档编辑器',
    'Save and references': '存档与参考数据', 'Open save': '打开存档',
    'Interface and game names': '界面与游戏名称',
    'Dating & nicknames': '交往与昵称',
    'Dating status (marriage candidates only)': '交往状态（仅限结婚候选人）',
    'NPC calls player': 'NPC 对玩家的称呼', 'Player calls NPC': '玩家对 NPC 的称呼',
    'Default for Lest': '雷斯特的默认称呼', 'Default for Frey': '芙蕾的默认称呼',
    '[Player name]': '[玩家姓名]',
    'Saved flags and nicknames only; does not simulate confessions, breakups, marriage or story events. Nicknames are independent of dating. Export dating cleanup, if enabled, overrides these fields for its targets. Guests are not supported here.': '仅修改已保存的标记与昵称，不模拟告白、分手、结婚或剧情事件。昵称与交往状态相互独立。若启用导出时的交往清理，将覆盖其目标人物的这些字段。此页不支持客串人物。',
    'Nickname labels use Game names, not Interface. Player-name tokens appear as [Player name].': '昵称文本跟随“游戏名称”，而非“界面”语言。玩家姓名占位符显示为 [玩家姓名]。',
    'Read game folder (or rf3TxtHeroNickName name tables) to load special nickname choices. Defaults and stored IDs remain available.': '请读取游戏目录（或 rf3TxtHeroNickName 名称表）以加载特殊昵称选项。默认称呼和已保存的编号仍可选择。',
    'Dating status is editable only for marriage candidates.': '仅结婚候选人可修改交往状态。',
    'Unknown relationship field.': '未知的人际关系字段。',
    'Unrecognized nickname table layout.': '无法识别的昵称表结构。',
    'Player name': '玩家姓名',
    'Player name (up to 6 characters / 18 UTF-8 bytes)': '玩家姓名（最多 6 个字符 / 18 个 UTF-8 字节）',
    'Reset player name to game default': '将玩家姓名重置为游戏默认',
    'Player names are stored in rf4_sys.sav, not individual slot files. Select the matching bank and save slot. Editing a name does not create a slot or change its gender.': '玩家姓名存储在 rf4_sys.sav 中，而非单独的存档槽文件。请选择对应的存档组与槽位。编辑姓名不会创建存档或改变性别。',
    'Blank uses the game default on the next load. Unsupported font glyphs may not display. Reset only prepares a draft; click Apply changes, then export the system save.': '留空会在下次加载时使用游戏默认姓名。字体不支持的字符可能无法显示。重置仅生成草稿；请点击“应用修改”，然后导出系统存档。',
    'Open rf4_sys.sav to edit player names. Individual slot files do not contain this field.': '请打开 rf4_sys.sav 编辑玩家姓名。单独的存档槽文件不含此字段。',
    'Open rf4_sys.sav to edit player names.': '请打开 rf4_sys.sav 编辑玩家姓名。',
    'Select an existing save-slot name record; this does not create a save.': '请选择已有存档的姓名记录；此操作不会创建存档。',
    'Stored name bytes are unrecognized; keep unless intentionally replacing.': '无法识别已保存的姓名字节；除非有意替换，否则请保留。',
    'Reset leaves the name empty so the game chooses its default from the loaded character gender and game language.': '重置会将姓名留空，由游戏按已加载角色的性别与游戏语言选择默认姓名。',
    '[Game default]': '[游戏默认]', '[Empty slot]': '[空存档槽]',
    'Player name must be text.': '玩家姓名必须为文本。',
    'Player name allows up to 6 characters, without control characters.': '玩家姓名最多 6 个字符，且不能含控制字符。',
    'Player name must fit in 18 UTF-8 bytes.': '玩家姓名不能超过 18 个 UTF-8 字节。',
    'Uncheck to hide the preview and make more room for item fields.': '取消勾选可收起预览，为物品字段留出更多空间。',
    'Undo': '撤销', 'Redo': '重做', 'Read game folder': '读取游戏目录',
    'Export edited save': '导出修改后的存档', 'Save overview': '存档概览',
    'Calendar': '日期', 'Player values': '玩家数值', 'Bag & storage': '背包与仓库',
    'Skills': '技能', 'Learned recipes': '已学配方', 'Friendship': '好感度',
    'People stats': '人物属性', 'Tamed monsters': '已驯服魔物', 'Trophy records': '奖杯记录',
    'Marriage flags': '婚姻标志', 'System save unlocks': '系统存档解锁',
    'Expert: story flags': '专家：剧情标志', 'Read-only item reference': '物品参考数据（只读）',
    'Expert: raw save fields': '专家：原始存档字段', 'Review & export': '检查与导出',
    'Enable editing': '启用编辑', 'No draft': '无待应用修改', 'Clear draft': '清除草稿',
    'Apply changes': '应用修改', 'Draft pending · apply or clear before export': '有待应用修改 · 导出前请应用或清除',
    'Blank keeps existing values': '留空保留原值', 'Enable this editor first.': '请先启用此编辑器。',
    'Choose a matching item from the list; typed names are not item IDs.': '请从列表选择匹配的物品；输入的名称不是物品 ID。',
    'Try synthetic demo': '试用演示存档', 'Read extracted item tables': '读取已提取的物品表',
    'Read extracted recipe tables': '读取已提取的配方表', 'Read extracted language names': '读取已提取的名称表',
    'No save loaded': '未加载存档', 'Open a save first.': '请先打开存档。',
    'Native desktop controls · offline · no browser or local server. Back up your save folder and close the game before editing.': '原生桌面界面 · 离线 · 无浏览器或本地服务器。编辑前请备份存档目录并关闭游戏。',
    'Changes applied in memory. Review and export; the original is untouched.': '修改已应用到内存。检查后导出；原文件未改动。',
    'Edit not applied': '修改未应用', 'Unexported changes': '尚未导出的修改',
    'Original loaded · no edits': '已加载原始存档 · 无修改',
    'Current edits exported': '当前修改已导出',
    'Demo · export disabled': '演示存档 · 禁止导出',
    'Discard unexported edits and drafts?': '放弃尚未导出的修改和草稿？',
    'Apply or clear drafts before export.': '导出前请应用或清除草稿。',
    'Download an edited copy; keep a backup.': '导出修改副本；请保留备份。',
    'Open a slot or system save': '打开槽位存档或系统存档',
    'Choose game folder containing Bundle': '选择包含 Bundle 的游戏目录',
    'Read extracted definition tables': '读取已提取的定义表', 'Read extracted name tables': '读取已提取的名称表',
    'Too many reference tables.': '参考表数量过多。', 'Reference table is too large.': '参考表过大。',
    'Read up to 21 name tables.': '一次最多读取 21 个名称表。',
    'Read up to 28 name tables.': '一次最多读取 28 个名称表。',
    'Choose supported game TEXT name tables.': '请选择支持的游戏 TEXT 名称表。',
    'Choose name tables, not descriptions.': '请选择名称表，而非描述表。',
    'Apply or clear drafts before replacing game references.': '替换游戏参考数据前请应用或清除草稿。',
    'Apply or clear drafts before reading game references.': '读取游戏参考数据前请应用或清除草稿。',
    'Apply or clear drafts before replacing references.': '替换参考数据前请应用或清除草稿。',
    'Direct date changes do not simulate daily game updates.': '直接修改日期不会模拟每日游戏更新。',
    'Day': '日', 'Season': '季节', 'Year': '年', 'Spring': '春', 'Summer': '夏', 'Autumn': '秋', 'Winter': '冬',
    'Money': '金钱', 'Lumber': '木材', 'Material stone': '石材', 'Fertilizer': '肥料',
    'Order points (prince/princess points)': '王子／公主点数', 'Order points': '王子／公主点数',
    'Maximum health': '最大 HP', 'Current health': '当前 HP', 'Maximum rune points': '最大 RP',
    'Current rune points': '当前 RP', 'Strength': '力量', 'Intelligence': '智力', 'Vitality': '体力',
    'Base values only; equipment-adjusted attributes are not recalculated.': '仅编辑基础数值；不会重新计算装备加成后的属性。',
    'Bag': '背包', 'Fridge': '冰箱', 'Storage': '仓库', 'Weapon box': '武器箱', 'Armor box': '防具箱',
    'Saved slots do not unlock capacity. Replacements clear previous metadata. Element changes append crystals without deleting existing upgrades; test equipment edits in-game.': '编辑槽位不会解锁容量。替换物品会清除原有附加数据。属性修改通过追加结晶完成，不删除已有强化；请在游戏中验证。',
    'Filter saved items by name or slot': '按名称或槽位筛选', 'Show empty slots': '显示空槽位',
    'Saved slot': '存档槽位', 'Item': '物品', 'Quantity': '数量', 'Levels': '等级', 'Empty': '空',
    'Item (type to search)': '物品（可输入搜索）', 'Set all item levels': '统一物品等级',
    'Weapon / tool element': '武器／工具属性', 'Keep existing': '保留原值',
    'Inherited equipment': '继承装备', 'Total-level bonus (0–150)': '总等级加成（0–150）',
    'Rarity bonus (0–200)': '稀有度加成（0–200）', 'None / remove · 0': '无／移除 · 0',
    'None · 0': '无 · 0', 'Empty / clear slot · 0': '空／清空槽位 · 0',
    'Non-elemental': '无属性', 'Fire': '火', 'Water': '水', 'Earth': '地', 'Wind': '风', 'Light': '光', 'Dark': '暗', 'Love': '爱',
    'Attachment IDs are 10-bit (0–1023), equipment only. Unchanged fields are preserved; 0 removes an attachment. Blank level preserves mixed unit levels.': '附加物品 ID 为 10 位（0–1023），仅限装备。未改字段保留；0 表示移除。等级留空保留各物品原等级。',
    'Apply or clear item drafts before switching containers.': '切换容器前请应用或清除物品草稿。',
    'Apply or clear item drafts before switching slots.': '切换槽位前请应用或清除物品草稿。',
    'Skill level': '技能等级', 'Experience (0–16,777,215)': '经验值（0–16,777,215）', 'Experience': '经验值',
    'Recipe learned': '已学会配方', 'Friendship level (0–10,000)': '好感度等级（0–10,000）',
    'Friendship (0–1,000)': '好感度（0–1,000）', 'Combat level': '战斗等级',
    'Recorded result': '记录结果', 'All groups': '全部分类', 'Filter recipe result names': '按配方产物名称筛选',
    'Learn filtered recipes': '学会筛选出的配方', 'Forget filtered recipes': '忘记筛选出的配方',
    'Learn all recipes': '学会全部配方',
    'Learn all loaded recipes, ignoring filters (Ctrl+Shift+L).': '学会已加载的全部配方，不受筛选限制（Ctrl+Shift+L）。',
    'All loaded recipes learned in memory. Export to save.': '已在内存中学会全部已加载配方。请导出以保存。',
    'Open a slot save first.': '请先打开槽位存档。',
    'Read recipe tables first.': '请先读取配方表。',
    'No recipes match the current filters.': '没有配方符合当前筛选条件。',
    'Direct skill levels do not award stat gains. Crafting / resistance skills cap at 99; others at 999.': '直接修改技能等级不会补发属性成长。制造／抗性技能上限 99，其余 999。',
    'Variants sharing a learned bit change together. Recipe difficulty is not stored as an editable save value.': '共用学习标志的配方变体会同时改变。配方难度不是可编辑的存档值。',
    'Does not trigger dating, wedding or story events.': '不会触发恋爱、婚礼或剧情事件。',
    'Stored base stats only; no spawning or derived-stat recalculation.': '仅编辑存储的基础属性；不会生成人物或重算派生属性。',
    'Existing tamed monsters only. Names, species and barns are preserved.': '仅限已驯服的魔物。名称、种类和兽舍保留。',
    'Recorded game results only, not physical trophies or Steam achievements.': '仅修改游戏结果记录，不是实体奖杯或 Steam 成就。',
    'Not recorded': '未记录', 'Recorded': '已记录', 'None': '无', 'Gold / first': '金／第一名',
    'Silver / second': '银／第二名', 'Bronze / third': '铜／第三名',
    'Clear or apply the recipe draft before selecting another recipe.': '选择其他配方前请清除或应用草稿。',
    'Apply or clear this draft before selecting another record.': '选择其他记录前请应用或清除草稿。',
    'Enable recipe editing and apply / clear its draft first.': '请先启用配方编辑并应用／清除草稿。',
    'Flags only—not a complete marry/divorce operation. Wedding events, pregnancy, children, schedules and system unlocks are not simulated. Back up and test the exported copy.': '仅修改标志，不是完整的结婚／离婚操作。不会模拟婚礼、怀孕、子女、日程或系统解锁。请备份并验证导出副本。',
    'Event candidate (does not change spouse)': '事件对象（不会改变配偶）', 'Spouse': '配偶',
    'Anniversary season': '结婚纪念季节', 'Anniversary day (0 = unset)': '结婚纪念日（0 = 未设置）',
    'Can receive engagement ring': '可接收订婚戒指', 'Anniversary conversation recorded': '已记录纪念日对话',
    'Wedding memory flag': '婚礼回忆标志', 'Candidate marriage event cleared': '对象结婚事件已完成',
    'Candidate newlywed event cleared': '对象新婚事件已完成',
    'Apply or clear marriage drafts before switching candidates.': '切换对象前请应用或清除婚姻草稿。',
    'Persistent ending/wedding/data-transfer records only. These do not simulate events or advance slot saves.': '仅修改持久的结局／婚礼／数据继承记录，不会模拟事件或推进槽位存档。',
    'Ending / extra orders recorded': '已记录结局／额外指令', 'Wedding variant 2 recorded': '已记录婚礼变体 2',
    'Wedding variant 3 recorded': '已记录婚礼变体 3', 'Final story record (meaning incomplete)': '最终剧情记录（含义未完全确认）',
    'Data-transfer order unlocked': '已解锁数据继承指令',
    'Story changes can break progression. These controls do not initialize world state, reward quests or replay events.': '剧情修改可能破坏进度。这些控件不会初始化世界状态、发放任务奖励或重播事件。',
    'Find flags / registers by developer name or description': '按开发者符号、中文说明或原描述搜索',
    'Value (1-bit flags: 0 or 1)': '值（单比特标志：0 或 1）', 'Read symbols': '读取符号表',
    'Download progress profile': '导出进度配置', 'Read and apply profile': '读取并应用配置',
    'Apply or clear the flag draft first.': '请先应用或清除标志草稿。',
    'Apply or clear drafts before replacing symbols.': '替换符号表前请应用或清除草稿。',
    'Read emdeb.bin': '读取 emdeb.bin', 'Symbol table is too large.': '符号表过大。',
    'Read progress profile': '读取进度配置', 'Progress profile is too large.': '进度配置过大。',
    'Enable flag editing and apply / clear drafts first.': '请先启用标志编辑并应用／清除草稿。',
    'Apply progression flags?': '应用进度标志？',
    'Game definitions are not saved instance stats. This does not edit game files.': '游戏定义不是物品实例的最终属性。不会修改游戏文件。',
    'Item ID': '物品 ID', 'Look up definitions': '查询定义',
    'Use only independently verified offsets. The checksum header is protected; raw edits may break the save.': '仅使用独立验证过的偏移。校验头受保护；原始字节修改可能损坏存档。',
    'File offset (decimal or 0x hex)': '文件偏移（十进制或 0x 十六进制）', 'Integer type': '整数类型',
    'New integer value': '新整数值', 'OR hex bytes to patch': '或：要修改的十六进制字节',
    'Enter either a number or space-separated two-digit hex bytes, not both. At most 256 raw bytes per edit.': '输入整数或用空格分隔的双位十六进制字节，不可同时输入。每次最多修改 256 字节。',
    'Inspect current integer': '查看当前整数', 'Enter either an integer or hex bytes.': '请输入整数或十六进制字节之一。',
    'Export creates a copy. Keep your backup; a correct checksum does not guarantee in-game acceptance.': '导出会创建副本。请保留备份；校验正确不代表游戏一定能正常读取。',
    'Keep source format': '保留源格式', 'PC (experimental if converting)': 'PC（转换为实验功能）',
    'Switch (experimental if converting)': 'Switch（转换为实验功能）', 'Output platform': '输出平台',
    'I accept experimental PC ↔ Switch conversion': '我接受实验性 PC ↔ Switch 转换',
    'Repair an invalid original checksum (does not recover damaged data)': '修复原存档校验错误（不能恢复损坏数据）',
    'Keep edited gender': '保留当前性别', 'Match original gender': '匹配原存档性别',
    'Male · Lest': '男主角 · 雷斯特', 'Female · Frey': '女主角 · 芙蕾', 'Gender on export': '导出性别',
    'Also reset appearance, portrait and outfit': '同时重置外观、立绘与服装',
    'Clear incompatible dating and their special nicknames (keep friendship)': '清除不兼容的恋爱关系及专用称呼（保留好感度）',
    'Optional: Lest clears the six bachelors; Frey clears the six bachelorettes. Both forms of address reset. Story/events, date history and other NPCs stay unchanged. Does not repair marriage.': '可选：雷斯特清除六位男恋爱对象，芙蕾清除六位女恋爱对象。双方称呼重置；剧情／事件、约会历史及其他 NPC 保留。不修复婚姻状态。',
    'Choose Male, Female or Match original gender for dating cleanup.': '清理恋爱关系前请选择男主角、女主角或匹配原性别。',
    'Original gender is unrecognized. Choose Male or Female explicitly.': '原存档性别无法识别，请明确选择男主角或女主角。',
    'Download original backup': '导出原始备份', 'Download change report': '导出修改报告',
    'Restore original in memory': '在内存中恢复原始存档', 'Save a new file — keep your backup': '保存新文件 — 请保留备份',
    'Open a real save first. Synthetic demo export is disabled.': '请先打开真实存档。演示存档禁止导出。',
    'Apply or clear all drafts before exporting, including disabled editors.': '导出前请应用或清除所有草稿，包括已禁用的编辑器。',
    'Edited save exported. Original source file was not automatically overwritten.': '修改副本已导出。原始文件未被自动覆盖。',
    'Enable gender correction before cleaning dating state.': '清理恋爱状态前请启用性别修正。',
    'Dating cleanup cannot handle this spouse. Resolve marriage separately; family/event state will not be erased.': '无法对当前配偶执行恋爱清理。请单独处理婚姻；不会清除家庭／事件状态。',
    'Read the item definition table before editing bag items.': '编辑物品前请读取物品定义表。',
    'Attachments are only editable on nonstackable equipment, not stacked items.': '附加材料仅适用于不可堆叠装备，不可用于堆叠物品。',
    'Not enough unused upgrade slots to change element without removing attachments.': '空余强化槽不足，无法在保留原材料的同时更改属性。',
    'Current health / rune points cannot exceed the maxima.': '当前 HP／RP 不能超过最大值。',
    'Acknowledge checksum repair before exporting this damaged save.': '导出此损坏存档前请确认修复校验。',
    'Short sword': '单手剑', 'Long sword': '双手剑', 'Spear': '枪', 'Axe / hammer': '斧／锤',
    'Dual blades': '双剑', 'Fist': '拳套', 'Farming': '农耕', 'Logging': '伐木', 'Mining': '采掘',
    'Fishing': '钓鱼', 'Cooking': '料理', 'Forging': '锻造', 'Chemistry': '药学', 'Crafting': '装饰',
    'Searching': '探索', 'Walking': '行走', 'Sleeping': '睡眠', 'Eating': '食事', 'Defense': '防御',
    'Resist poison': '毒抗性', 'Resist seal': '封印抗性', 'Resist paralysis': '麻痹抗性',
    'Resist sleep': '睡眠抗性', 'Resist fatigue': '疲劳抗性', 'Resist cold': '感冒抗性',
    'Resist knockout': '即死抗性', 'Bathing': '洗澡', 'Taming': '饲育', 'Throwing': '投掷',
    'Leadership': '领导', 'Bartering': '交易',
    'Item effect preview': '物品效果预览', 'Current item': '当前物品', 'Draft result': '草稿结果',
    'Preview only — no save bytes or undo history are changed.': '仅预览，不修改存档字节或撤销历史。',
    'Definition-based preview, not final in-game stats.': '基于定义的预览，不是游戏内最终属性。',
    'Read your game equipment / use / upgrade tables to preview effects.': '请读取游戏装备／使用／强化定义表以预览效果。',
    'Base equipment parameters': '装备基础参数', 'Inherited equipment parameters': '继承装备参数',
    'Base use effects': '基础使用效果', 'Raw material bonuses': '材料原始加成',
    'Not simulated: repeated-material penalties, material levels, total-level/rarity bonuses, special upgrade multipliers, inheritance combinations and actor stats.': '未模拟：重复材料衰减、材料等级、总等级／稀有度加成、特殊强化倍率、继承组合及人物属性。',
    'No nonzero effects in this reference record.': '此参考记录无非零效果。',
    'Unknown bits': '未知位', 'Raw': '原始值', 'Effect': '效果', 'Value': '值',
    'Preview unavailable': '无法预览', 'Final stats unknown': '最终属性未确认',
    'Item-level scaling and cooking combinations are not simulated.': '未模拟物品等级缩放及料理组合。',
    'game minutes': '游戏分钟', 'Dizzy': '眩晕值', 'Critical chance': '暴击率',
    'Knockback': '击退', 'Stun duration': '硬直持续时间', 'HP recovery': 'HP 回复',
    'RP recovery': 'RP 回复', 'Max HP': '最大 HP', 'Max RP': '最大 RP',
    'Permanent HP': '永久 HP', 'Permanent STR': '永久力量', 'Permanent INT': '永久智力',
    'Permanent VIT': '永久体力', 'Effect duration': '效果持续时间',
    'Per-level scaling reference': '每级缩放参数（参考）', 'Attack range': '攻击范围',
    'Attack arc': '攻击角度', 'Upgrade difficulty': '强化难度',
    'Poison': '毒', 'Seal': '封印', 'Paralysis': '麻痹', 'Sleep': '睡眠', 'Fatigue': '疲劳',
    'Sick': '感冒', 'Instant death': '即死', 'HP drain': 'HP 吸收', 'Physical': '物理', 'Critical': '暴击',
    'Magic': '魔法攻击', 'DirectPlayerDamage': '直接伤害玩家（含义未确认）',
    'IgnoreDefense': '忽略防御（取决于装备类型）', 'NoSpread': '无随机伤害浮动（未确认）',
    'HammerSound': '锤击音效', 'FullStun': '忽略硬直抗性', 'TurnipEffect': '芜菁特效',
    'MarionettaGrab': '玛丽奈塔抓取', 'WaterSound': '水音效', 'DropRateUp': '提高掉落率',
    'WhiteStone': '白石：配偶／子女伤害加成', 'MinimumDamage': '每击固定 1 点伤害',
    'HalfElementRes': '属性抗性减半', 'FaintDropCabbage': '击倒后掉落卷心菜',
    'FaintDropPumpkin': '击倒后掉落南瓜', 'FaintDropPotato': '击倒后掉落土豆',
    'FaintDropTurnip': '击倒后掉落芜菁', 'MagnifyingGlass': '显示土壤／作物详情',
    'Lightweight': '双手武器可获得部分盾牌加成', 'NoCrits': '不会暴击',
    'WaterWalking': '水上行走', 'AggroRangeDown': '降低魔物警戒范围',
    'DashDistanceUp': '增加冲刺距离', 'FreeFarming': '不受格子限制播种',
    'ChirpOnStep': '走路鸣叫', 'BrakingSpeedDown': '降低停止速度',
    'DashAttackDisabled': '禁用冲刺攻击', 'BrakingSpeedUp': '提高停止速度',
    'Clumsy': '偶尔跌倒', 'HeightUp': '增加身高', 'MovementSpeedUp': '提高移动速度',
    'MovementSpeedUpMore': '大幅提高移动速度', 'MovementSpeedDown': '降低移动速度',
    'ResistWeakWind': '抵抗部分弱风', 'DashInvincibilityUp': '延长冲刺无敌时间',
    'ChargeSpeedUp': '加快蓄力', 'ThrowDistanceUp': '增加投掷距离',
    'YawnDisabled': '不打哈欠', 'MonsterStatsUp': '提高魔物队友属性',
    'CompanionStatsUp': '提高人物队友属性', 'FarmToolAttackUp': '提高农具攻击力',
    'LevelXpGainUp': '提高战斗经验获取', 'SkillXpGainUp': '提高技能经验获取',
    'RpCostDown': '减少 RP 消耗', 'RpCostDownMore': '大幅减少 RP 消耗',
    'NullDamageChance': '概率只受 1 点伤害', 'BestAttack': '使用较高的物理／魔法攻击',
    'MaxHpUp': '提高最大 HP', 'NoMonsterSpawns': '不生成随机魔物（Boss 除外）',
    'ReverseStatus': '反转部分异常状态效果', 'HpRegen': '周期回复 HP', 'RpRegen': '周期回复 RP',
    'FlinchTimeDown': '缩短受击硬直', 'HitRangeUp': '增加攻击范围',
    'PhysicalDamageDown': '降低无属性伤害', 'RecoveryUp': '提高回复物品效果',
    'HealPoison': '解除毒', 'HealSeal': '解除封印', 'HealParalysis': '解除麻痹',
    'HealSleep': '解除睡眠', 'HealFatigue': '解除疲劳', 'HealSick': '解除感冒',
    'CausePoison': '造成毒', 'CauseSeal': '造成封印', 'CauseParalysis': '造成麻痹',
    'CauseSleep': '造成睡眠', 'CauseFatigue': '造成疲劳', 'CauseSick': '造成感冒',
    'CauseFaint': '造成即死', 'LevelUp': '升级', 'Unknown4000': '未知状态位 0x4000',
    'not recognized / not a weapon': '无法识别／不是武器',
    'Main story': '主线剧情', 'Town events': '城镇事件', 'Requests': '委托',
    'Other developer flags': '其他开发者标志', 'All flags': '全部标志',
    'Evidence / edit impact': '证据／修改影响', 'Original developer description': '开发者原始说明',
    'Translation / interpretation only; not gameplay validation.': '仅为翻译／释义，不代表已在游戏中验证。',
    'Curated translation; not gameplay validation.': '人工翻译；不是游戏内验证结果。',
    'Symbol interpretation only; meaning unverified.': '仅按符号释义；实际含义未验证。',
    'Developer description / symbol; not gameplay validation': '开发者说明／符号；不是游戏内验证结果',
    'CT label; semantics not independently verified': 'CT 标签；含义尚未独立验证',
    'Unknown or mismatched layout': '未知或不匹配的布局',
    'Story Event Flags': '剧情事件标志', 'Story Barrier Flags': '剧情屏障标志',
    'Dungeon Barrier Flags': '迷宫屏障标志', 'Chest Flags': '宝箱标志', 'Reference flags': '参考标志',
    'WARNING: story rewind bypasses the game advance-only guard.': '警告：剧情回退会绕过游戏“只向前推进”的保护。',
    'Static game/script evidence; not in-game validation': '游戏／脚本静态证据；不是游戏内验证结果',
    'Script witness (not a playable preset)': '脚本节点证据（不是可玩的预设）',
    'Pass': '满足', 'Fail': '不满足', 'Progress gate': '进度条件',
    'Not-completed gate': '未完成条件', 'Overall eligibility': '总体资格',
    'unknown': '未知', 'false': '不满足',
    'Participant-enable queries unresolved; not assumed to be friendship checks.': '参与者启用查询尚未解析；不会假定为好感度检查。',
    'Unknown meaning — keep the original developer symbol.': '含义未确认 — 保留开发者原始符号。',
    'No automatic event replay, rewards, world initialization or dependency repair.': '不会自动重播事件、发放奖励、初始化世界或修复依赖。',
    'Story jump planner': '剧情跳转规划器',
    'Individual flags / registers': '单独的标志／寄存器',
    'Target story stage (0–511)': '目标剧情阶段（0–511）',
    'Explicit supporting flags (JSON object; blank keeps other flags)': '明确指定的关联标志（JSON 对象；留空保留其他标志）',
    'I understand this does not reconstruct a playable checkpoint': '我理解这不会重建可玩的剧情检查点',
    'Allow rewind (later world state is not reverted)': '允许回退（后续世界状态不会还原）',
    'Choose a script witness (not a preset)': '选择脚本节点证据（不是预设）',
    'Story profile staged. Review the jump preview and acknowledge incomplete dependencies.': '剧情档案已暂存。请查看跳转预览并确认依赖尚未完整处理。',
    'Acknowledge incomplete story dependencies before applying a jump.': '应用跳转前请确认依赖尚未完整处理。',
    'Explicitly allow story rewind before decreasing the stage.': '降低剧情阶段前请明确允许回退。',
    'Profile story stage conflicts with the jump target.': '档案中的剧情阶段与跳转目标冲突。',
    'Stage end-game flags (experimental)': '暂存终局标志（实验性）',
    'Apply or clear the story draft before choosing a shortcut.': '选择快捷操作前请应用或清除剧情草稿。',
    'End-game flags staged only. Review omitted actions and acknowledge risk before applying.': '仅暂存终局标志。请检查不会执行的操作，并确认风险后再应用。',
    'Experimental non-candidate flags (no romance scripts added)': '实验性：非恋爱对象标志（不添加恋爱脚本）',
    'Saved dating status': '存储的交往状态',
    ' · experimental': ' · 实验性',
    'Experimental spouse IDs only change a five-bit register. Non-candidates have no wedding/romance scripts; guests may not work. IDs above 31 cannot be stored.': '实验性配偶 ID 只修改五位寄存器。非恋爱对象没有婚礼／恋爱脚本，客串人物可能无效。无法存储大于 31 的 ID。',
    'Dating outside marriage candidates requires experimental consent.': '修改非恋爱对象的交往标志需要确认实验性风险。',
    'Non-candidate spouse IDs require experimental consent.': '设置非恋爱对象的配偶 ID 需要确认实验性风险。',
    'Soil editor': '土壤编辑', 'Soil patch': '土壤区块',
    'Raw packed soil values, not crop growth or a magnifying-glass simulator. One patch covers shared soil. Crop records and unused patches are preserved. Back up and test in-game.': '编辑土壤原始位字段，不模拟作物成长或放大镜数值。每个区块为共享土壤。保留作物记录及未使用区块；请备份并在游戏内测试。',
    'Apply changed fields to every used patch on this field': '将改动的字段应用到此农田所有已使用区块',
    'Prepare soil health 255': '准备土壤健康值 255',
    'Center field': '中央农田', 'Bottom-left field': '左下农田', 'Bottom-right field': '右下农田', 'Top-left field': '左上农田', 'Top-right field': '右上农田',
    'Spring field': '春之田', 'Summer field': '夏之田', 'Autumn field': '秋之田', 'Winter field': '冬之田',
    'Growth boost (raw 0–127)': '成长增益（原始值 0–127）',
    'Yield magnitude (raw 0–1,023)': '产量幅度（原始值 0–1,023）', 'Yield sign bit': '产量符号位',
    'Quality magnitude (raw 0–511)': '品质幅度（原始值 0–511）', 'Quality sign bit': '品质符号位',
    'Size magnitude (raw 0–511)': '大小幅度（原始值 0–511）', 'Size sign bit': '大小符号位',
    'Soil defense (raw 0–63)': '土壤防御（原始值 0–63）', 'Soil health (raw 0–255)': '土壤健康（原始值 0–255）',
    'Base yield level (raw 0–15)': '基础产量等级（原始值 0–15）', 'Base quality level (raw 0–15)': '基础品质等级（原始值 0–15）',
    'Base size level (raw 0–15)': '基础大小等级（原始值 0–15）', 'Overall progress (raw 0–127)': '综合进度（原始值 0–127）',
    'Speed progress (raw 0–127)': '速度进度（原始值 0–127）', 'Yield progress (raw 0–127)': '产量进度（原始值 0–127）',
    'Quality progress (raw 0–127)': '品质进度（原始值 0–127）', 'Size progress (raw 0–127)': '大小进度（原始值 0–127）',
    'Overall level (raw 0–15)': '综合等级（原始值 0–15）', 'Base speed level (raw 0–15)': '基础速度等级（原始值 0–15）',
    'Add roster NPC / monster': '添加名册 NPC／魔物',
    'Experimental: writes an empty tamed-monster slot, not the town NPC. NPC species may fail to spawn or lack monster AI, riding and produce. No new game definitions are created. Requires a built barn room with space.': '实验性：写入空的驯服魔物栏位，不修改城镇 NPC。NPC 种类可能无法生成，或缺少魔物 AI、骑乘及产物。不会创建新游戏定义。需要已建造且有空位的魔物小屋。',
    'NPC / monster species (1–255; not all IDs are valid actors)': 'NPC／魔物种类（1–255；不是所有 ID 都是有效角色）',
    'Roster name (up to 6 characters / 18 UTF-8 bytes)': '名册名称（最多 6 个字符／18 UTF-8 字节）',
    'Blank generates a short default name': '留空生成简短的默认名称',
    'Empty destination slot': '目标空栏位', 'Built barn room': '已建造的小屋房间',
    'Stat source': '属性来源', 'Basic level 1 (not species-scaled)': '基础 1 级（不按种类缩放）',
    'Existing monster stats': '已有魔物属性', 'Existing NPC stats': '已有 NPC 属性',
    'Source ID (NPC 1–26 / monster slot 0–199)': '来源 ID（NPC 1–26／魔物栏位 0–199）',
    'I accept experimental roster compatibility risks': '我接受实验性名册兼容风险',
    'Barn': '小屋', 'Room': '房间', 'Free barn places': '小屋空位',
    'Acknowledge experimental roster creation first.': '请先确认实验性名册创建风险。',
    'Choose an empty monster roster slot. Existing monsters are never overwritten.': '请选择空的魔物名册栏位，不覆盖已有魔物。',
    'Build a barn room with a free place first (four monsters per room).': '请先建造有空位的小屋房间（每间 4 只魔物）。',
    'Reset NPC calls player': '重置 NPC 对玩家称呼',
    'Reset player calls NPC': '重置玩家对 NPC 称呼',
    'Reset both for current gender': '按当前性别重置双方称呼',
    'Nickname reset target: Lest': '称呼重置目标：雷斯特（Lest）',
    'Nickname reset target: Frey': '称呼重置目标：芙蕾（Frey）',
    'Nickname reset unavailable: no recognized slot gender': '无法重置称呼：未读取到可识别的栏位性别',
    'Uses current saved gender, not appearance or export gender. Only stages nickname defaults; dating and friendship stay unchanged.': '使用当前存储的性别，而非外观或导出性别。仅暂存默认称呼，交往及好感度不变。',
    'Nickname defaults staged only. Apply or export to save; dating and friendship stay unchanged.': '仅暂存默认称呼。请应用或导出保存；交往及好感度不变。',
    'Saved gender is unrecognized. Cannot choose Lest / Frey nickname defaults.': '无法识别存储的性别，不能选择雷斯特／芙蕾的默认称呼。',
}

PATTERNS = [
    (r'Bank (\d+) · slot (\d+)', '存档组 {0} · 槽位 {1}'),
    (r'Stored nickname ID (\d+) · keep unless verified', '已保存的昵称编号 {0} · 未验证前请保留'),
    (r'native-save: Error: (.+) \(line (\d+)\)', '{0}（行 {1}）'),
    (r'(.+) must be a whole number from (.+) to (.+)\.', '{0}必须是 {1} 到 {2} 之间的整数。'),
    (r'(.+) is required\.', '必须填写{0}。'),
    (r'(.+) must be a number\.', '{0}必须是数值。'),
    (r'(.+) infliction / attack', '{0}攻击附加'),
    (r'(.+) resistance', '{0}抗性'),
    (r'(.+) · cooking ingredient', '{0} · 料理附加材料'),
    (r'Crafting attachment (\d+)', '制作附加材料 {0}'),
    (r'Upgrade (\d+) · level (\d+)', '强化 {0} · 等级 {1}'),
    (r'Unrecognized stored ID (\d+)', '无法识别的存档 ID {0}'),
    (r'Unrecognized stored value (.+) · keep unless verified', '无法识别的存档值 {0} · 未验证前请保留'),
    (r'Unknown item (\d+)', '未知物品 {0}'),
    (r'(.+)–(.+); whole numbers only', '{0}–{1}；仅限整数'),
    (r'Apply (\d+) named flags as one undoable edit\? Events and world state will not be simulated\.', '将 {0} 个标志作为一次可撤销修改应用？不会模拟事件和世界状态。'),
    (r'Will clear dating / reset addresses: (.+)\. Friendship and event history stay unchanged\.', '将清除恋爱关系／重置称呼：{0}。好感度和事件历史保留。'),
    (r'Saved slot (\d+) · (.+) · current element: (.+)\.', '存档槽位 {0} · {1} · 当前属性：{2}。'),
    (r'Bit (\d+) · (\d+) bits · range 0–(\d+)', '起始位 {0} · 宽度 {1} 位 · 范围 0–{2}'),
    (r'(.+) · ([\d,]+) changed bytes · (\d+) undoable edits', '{0} · 已修改 {1} 字节 · {2} 次可撤销修改'),
    (r'([A-Z]+) · ([\d,]+) bytes · CRC valid', '{0} · {1} 字节 · CRC 有效'),
    (r'([A-Z]+) · ([\d,]+) bytes · CRC mismatch \(repair consent required\)', '{0} · {1} 字节 · CRC 不匹配（需确认修复）'),
    (r'([\d,]+) changed bytes · (\d+) undoable edits', '已修改 {0} 字节 · {1} 次可撤销修改'),
    (r'First (\d+) of (\d+) ranges shown; the JSON report includes all\.', '显示前 {0}／{1} 个区域；JSON 报告包含全部。'),
    (r'(.+) must be a whole number\.', '{0}必须是整数。'),
    (r'(.+) must be (.+)–(.+)\.', '{0}必须在 {1}–{2} 之间。'),
]


class UiLanguage:
    def __init__(self, code='en'):
        self.code = code

    def text(self, text):
        text = str(text)
        if self.code != 'zh-CN': return text
        if text in ZH: return ZH[text]
        for pattern, target in PATTERNS:
            match = re.fullmatch(pattern, text, re.DOTALL)
            if match: return target.format(*(self.text(value) for value in match.groups()))
        # Multiline status captions use whole-line translation, not substitutions
        # inside arbitrary user names, paths, developer identifiers or JSON.
        if '\n' in text: return '\n'.join(self.text(line) for line in text.split('\n'))
        return text

    def set_text(self, widget, source):
        translated = self.text(source)
        widget.setText(translated)
        entries = getattr(widget, '_ui_captions', {})
        entries['text'] = source, translated
        widget._ui_captions = entries

    def apply(self, root):
        from PySide6.QtCore import Qt, QSignalBlocker
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QLabel, QAbstractButton, QLineEdit, QGroupBox, QComboBox, QListWidget, QTableWidget, QWidget, QTabWidget
        role = int(Qt.ItemDataRole.UserRole) + 40

        def caption(obj, key, getter, setter):
            entries = getattr(obj, '_ui_captions', {})
            current = getter()
            source, last = entries.get(key, (current, current))
            if current != last: source = current
            translated = self.text(source)
            if translated != current: setter(translated)
            entries[key] = source, translated
            obj._ui_captions = entries

        def item_caption(item):
            if item is None: return
            current = item.text()
            entry = item.data(role)
            source = entry[0] if entry and current == entry[1] else current
            translated = self.text(source)
            item.setText(translated)
            item.setData(role, [source, translated])

        for obj in [root, *root.findChildren(QWidget), *root.findChildren(QAction)]:
            if isinstance(obj, (QLabel, QAbstractButton, QAction)):
                caption(obj, 'text', obj.text, obj.setText)
            if isinstance(obj, QLineEdit):
                caption(obj, 'placeholder', obj.placeholderText, obj.setPlaceholderText)
            if isinstance(obj, QGroupBox): caption(obj, 'title', obj.title, obj.setTitle)
            if isinstance(obj, QTabWidget):
                for index in range(obj.count()):
                    caption(obj, f'tab{index}', lambda index=index: obj.tabText(index), lambda text, index=index: obj.setTabText(index, text))
            caption(obj, 'tooltip', obj.toolTip, obj.setToolTip)
            if isinstance(obj, QComboBox):
                if obj.property('gameNames'): continue
                with QSignalBlocker(obj):
                    typed = obj.currentText() if obj.isEditable() and obj.currentText() != obj.itemText(obj.currentIndex()) else None
                    for index in range(obj.count()):
                        current = obj.itemText(index)
                        entry = obj.itemData(index, role)
                        source = entry[0] if entry and current == entry[1] else current
                        translated = self.text(source) if source in ZH or source.startswith(('Unrecognized stored', 'Unknown item', 'Crafting attachment', 'Upgrade ')) else source
                        if translated != current: obj.setItemText(index, translated)
                        obj.setItemData(index, [source, translated], role)
                    if typed is not None: obj.setEditText(typed)
            if isinstance(obj, QListWidget):
                for index in range(obj.count()): item_caption(obj.item(index))
            if isinstance(obj, QTableWidget):
                with QSignalBlocker(obj):
                    for column in range(obj.columnCount()): item_caption(obj.horizontalHeaderItem(column))
        caption(root, 'windowTitle', root.windowTitle, root.setWindowTitle)


def install_qt_translator(ui, parent):
    """Translate standard Qt buttons without packaging Qt's large locale bundle."""
    from PySide6.QtCore import QCoreApplication, QTranslator
    class CatalogTranslator(QTranslator):
        def isEmpty(self):
            return False
        def translate(self, context, sourceText, disambiguation=None, n=-1):
            # An empty Python string is a successful (blank) Qt translation,
            # not a missing catalog entry. Keep English/unmapped captions visible.
            return ui.text(sourceText) if ui.code == 'zh-CN' and sourceText in ZH else sourceText
    translator = CatalogTranslator(parent)
    QCoreApplication.instance().installTranslator(translator)
    return translator

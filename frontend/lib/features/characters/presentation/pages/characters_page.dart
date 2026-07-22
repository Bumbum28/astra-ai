import 'package:astra_ai/features/characters/application/roleplay_catalog_controller.dart';
import 'package:astra_ai/features/characters/domain/entities/character.dart';
import 'package:astra_ai/features/characters/domain/entities/persona.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CharactersPage extends ConsumerWidget {
  const CharactersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final catalog = ref.watch(roleplayCatalogControllerProvider);
    return DefaultTabController(
      length: 2,
      child: Column(
        children: <Widget>[
          Material(
            color: Theme.of(context).colorScheme.surface,
            child: SafeArea(
              bottom: false,
              child: Column(
                children: <Widget>[
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 12, 8),
                    child: Row(
                      children: <Widget>[
                        Expanded(
                          child: Text(
                            'Character System',
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ),
                        IconButton(
                          tooltip: 'Làm mới',
                          onPressed: () => ref
                              .read(roleplayCatalogControllerProvider.notifier)
                              .refreshCatalog(),
                          icon: const Icon(Icons.refresh),
                        ),
                      ],
                    ),
                  ),
                  const TabBar(
                    tabs: <Widget>[
                      Tab(icon: Icon(Icons.groups), text: 'Nhân vật'),
                      Tab(icon: Icon(Icons.badge_outlined), text: 'Persona'),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: catalog.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stackTrace) => _LoadError(
                onRetry: () => ref
                    .read(roleplayCatalogControllerProvider.notifier)
                    .refreshCatalog(),
              ),
              data: (state) => TabBarView(
                children: <Widget>[
                  _CharacterTab(items: state.characters),
                  _PersonaTab(items: state.personas),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CharacterTab extends ConsumerWidget {
  const _CharacterTab({required this.items});

  final List<CharacterProfile> items;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CatalogList<CharacterProfile>(
      items: items,
      emptyIcon: Icons.groups_outlined,
      emptyText: 'Chưa có nhân vật nào.',
      addLabel: 'Tạo nhân vật',
      onAdd: () => _edit(context, ref, null),
      itemBuilder: (context, item) => Card(
        child: ListTile(
          leading: CircleAvatar(
            child: Text(item.name.characters.first.toUpperCase()),
          ),
          title: Text(item.name),
          subtitle: Text(
            item.summary?.isNotEmpty == true
                ? '${item.summary}\nVersion ${item.currentVersion}'
                : 'Version ${item.currentVersion}',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          isThreeLine: item.summary?.isNotEmpty == true,
          trailing: PopupMenuButton<String>(
            onSelected: (value) async {
              if (value == 'edit') {
                await _edit(context, ref, item);
              } else if (value == 'archive') {
                await _archive(context, ref, item);
              }
            },
            itemBuilder: (context) => const <PopupMenuEntry<String>>[
              PopupMenuItem(value: 'edit', child: Text('Chỉnh sửa')),
              PopupMenuItem(value: 'archive', child: Text('Lưu trữ')),
            ],
          ),
          onTap: () => _edit(context, ref, item),
        ),
      ),
    );
  }

  Future<void> _edit(
    BuildContext context,
    WidgetRef ref,
    CharacterProfile? current,
  ) async {
    final data = await showDialog<Map<String, Object?>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => _CharacterEditor(current: current),
    );
    if (data == null) {
      return;
    }
    await ref
        .read(roleplayCatalogControllerProvider.notifier)
        .saveCharacter(current: current, data: data);
  }

  Future<void> _archive(
    BuildContext context,
    WidgetRef ref,
    CharacterProfile item,
  ) async {
    final confirmed = await _confirmArchive(context, item.name);
    if (confirmed) {
      await ref
          .read(roleplayCatalogControllerProvider.notifier)
          .archiveCharacter(item.id);
    }
  }
}

class _PersonaTab extends ConsumerWidget {
  const _PersonaTab({required this.items});

  final List<PersonaProfile> items;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _CatalogList<PersonaProfile>(
      items: items,
      emptyIcon: Icons.badge_outlined,
      emptyText: 'Chưa có persona nào.',
      addLabel: 'Tạo persona',
      onAdd: () => _edit(context, ref, null),
      itemBuilder: (context, item) => Card(
        child: ListTile(
          leading: const CircleAvatar(child: Icon(Icons.person_outline)),
          title: Text(item.name),
          subtitle: Text(
            [
              if (item.pronouns?.isNotEmpty == true) item.pronouns,
              'Version ${item.currentVersion}',
              if (item.description?.isNotEmpty == true) item.description,
            ].whereType<String>().join(' · '),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          trailing: PopupMenuButton<String>(
            onSelected: (value) async {
              if (value == 'edit') {
                await _edit(context, ref, item);
              } else if (value == 'archive') {
                await _archive(context, ref, item);
              }
            },
            itemBuilder: (context) => const <PopupMenuEntry<String>>[
              PopupMenuItem(value: 'edit', child: Text('Chỉnh sửa')),
              PopupMenuItem(value: 'archive', child: Text('Lưu trữ')),
            ],
          ),
          onTap: () => _edit(context, ref, item),
        ),
      ),
    );
  }

  Future<void> _edit(
    BuildContext context,
    WidgetRef ref,
    PersonaProfile? current,
  ) async {
    final data = await showDialog<Map<String, Object?>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => _PersonaEditor(current: current),
    );
    if (data == null) {
      return;
    }
    await ref
        .read(roleplayCatalogControllerProvider.notifier)
        .savePersona(current: current, data: data);
  }

  Future<void> _archive(
    BuildContext context,
    WidgetRef ref,
    PersonaProfile item,
  ) async {
    final confirmed = await _confirmArchive(context, item.name);
    if (confirmed) {
      await ref
          .read(roleplayCatalogControllerProvider.notifier)
          .archivePersona(item.id);
    }
  }
}

class _CatalogList<T> extends StatelessWidget {
  const _CatalogList({
    required this.items,
    required this.emptyIcon,
    required this.emptyText,
    required this.addLabel,
    required this.onAdd,
    required this.itemBuilder,
  });

  final List<T> items;
  final IconData emptyIcon;
  final String emptyText;
  final String addLabel;
  final VoidCallback onAdd;
  final Widget Function(BuildContext, T) itemBuilder;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: <Widget>[
        if (items.isEmpty)
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(emptyIcon, size: 64),
                const SizedBox(height: 12),
                Text(emptyText),
              ],
            ),
          )
        else
          ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
            itemCount: items.length,
            itemBuilder: (context, index) => itemBuilder(context, items[index]),
          ),
        Positioned(
          right: 20,
          bottom: 20,
          child: FloatingActionButton.extended(
            onPressed: onAdd,
            icon: const Icon(Icons.add),
            label: Text(addLabel),
          ),
        ),
      ],
    );
  }
}

class _CharacterEditor extends StatefulWidget {
  const _CharacterEditor({this.current});

  final CharacterProfile? current;

  @override
  State<_CharacterEditor> createState() => _CharacterEditorState();
}

class _CharacterEditorState extends State<_CharacterEditor> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name;
  late final TextEditingController _summary;
  late final TextEditingController _personality;
  late final TextEditingController _speakingStyle;
  late final TextEditingController _scenario;
  late final TextEditingController _greeting;
  late final TextEditingController _instructions;

  @override
  void initState() {
    super.initState();
    final item = widget.current;
    _name = TextEditingController(text: item?.name);
    _summary = TextEditingController(text: item?.summary);
    _personality = TextEditingController(text: item?.personality);
    _speakingStyle = TextEditingController(text: item?.speakingStyle);
    _scenario = TextEditingController(text: item?.scenario);
    _greeting = TextEditingController(text: item?.greeting);
    _instructions = TextEditingController(text: item?.systemInstructions);
  }

  @override
  void dispose() {
    for (final controller in <TextEditingController>[
      _name,
      _summary,
      _personality,
      _speakingStyle,
      _scenario,
      _greeting,
      _instructions,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.current == null ? 'Tạo nhân vật' : 'Sửa nhân vật'),
      content: SizedBox(
        width: 680,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                _field(_name, 'Tên nhân vật', required: true),
                _field(_summary, 'Tóm tắt', lines: 2),
                _field(_personality, 'Tính cách', lines: 4),
                _field(_speakingStyle, 'Phong cách nói', lines: 3),
                _field(_scenario, 'Bối cảnh', lines: 4),
                _field(_greeting, 'Lời chào mở đầu', lines: 3),
                _field(_instructions, 'Chỉ dẫn bổ sung', lines: 4),
              ],
            ),
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(onPressed: _submit, child: const Text('Lưu')),
      ],
    );
  }

  Widget _field(
    TextEditingController controller,
    String label, {
    int lines = 1,
    bool required = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        maxLines: lines,
        decoration: InputDecoration(labelText: label),
        validator: required
            ? (value) => value == null || value.trim().isEmpty
                  ? 'Không được để trống.'
                  : null
            : null,
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    Navigator.of(context).pop(<String, Object?>{
      'name': _name.text.trim(),
      'summary': _nullable(_summary.text),
      'personality': _nullable(_personality.text),
      'speaking_style': _nullable(_speakingStyle.text),
      'scenario': _nullable(_scenario.text),
      'greeting': _nullable(_greeting.text),
      'system_instructions': _nullable(_instructions.text),
    });
  }
}

class _PersonaEditor extends StatefulWidget {
  const _PersonaEditor({this.current});

  final PersonaProfile? current;

  @override
  State<_PersonaEditor> createState() => _PersonaEditorState();
}

class _PersonaEditorState extends State<_PersonaEditor> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _name;
  late final TextEditingController _description;
  late final TextEditingController _pronouns;
  late final TextEditingController _background;
  late final TextEditingController _traits;
  late final TextEditingController _writingStyle;

  @override
  void initState() {
    super.initState();
    final item = widget.current;
    _name = TextEditingController(text: item?.name);
    _description = TextEditingController(text: item?.description);
    _pronouns = TextEditingController(text: item?.pronouns);
    _background = TextEditingController(text: item?.background);
    _traits = TextEditingController(text: item?.traits);
    _writingStyle = TextEditingController(text: item?.writingStyle);
  }

  @override
  void dispose() {
    for (final controller in <TextEditingController>[
      _name,
      _description,
      _pronouns,
      _background,
      _traits,
      _writingStyle,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.current == null ? 'Tạo persona' : 'Sửa persona'),
      content: SizedBox(
        width: 680,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                _field(_name, 'Tên persona', required: true),
                _field(_pronouns, 'Đại từ / cách xưng hô'),
                _field(_description, 'Mô tả', lines: 3),
                _field(_background, 'Bối cảnh cá nhân', lines: 4),
                _field(_traits, 'Đặc điểm', lines: 3),
                _field(_writingStyle, 'Cách viết mong muốn', lines: 3),
              ],
            ),
          ),
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(onPressed: _submit, child: const Text('Lưu')),
      ],
    );
  }

  Widget _field(
    TextEditingController controller,
    String label, {
    int lines = 1,
    bool required = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        maxLines: lines,
        decoration: InputDecoration(labelText: label),
        validator: required
            ? (value) => value == null || value.trim().isEmpty
                  ? 'Không được để trống.'
                  : null
            : null,
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    Navigator.of(context).pop(<String, Object?>{
      'name': _name.text.trim(),
      'description': _nullable(_description.text),
      'pronouns': _nullable(_pronouns.text),
      'background': _nullable(_background.text),
      'traits': _nullable(_traits.text),
      'writing_style': _nullable(_writingStyle.text),
    });
  }
}

class _LoadError extends StatelessWidget {
  const _LoadError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(Icons.cloud_off_outlined, size: 52),
          const SizedBox(height: 12),
          const Text('Không tải được Character System.'),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: onRetry, child: const Text('Thử lại')),
        ],
      ),
    );
  }
}

Future<bool> _confirmArchive(BuildContext context, String name) async {
  return await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Lưu trữ mục này?'),
          content: Text('“$name” sẽ không còn xuất hiện trong danh sách chọn.'),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Lưu trữ'),
            ),
          ],
        ),
      ) ??
      false;
}

String? _nullable(String value) {
  final normalized = value.trim();
  return normalized.isEmpty ? null : normalized;
}

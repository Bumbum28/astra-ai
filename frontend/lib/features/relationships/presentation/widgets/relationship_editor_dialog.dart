import 'package:astra_ai/features/relationships/domain/entities/relationship.dart';
import 'package:flutter/material.dart';

class RelationshipEditorDialog extends StatefulWidget {
  const RelationshipEditorDialog({required this.current, super.key});

  final RelationshipProfile current;

  @override
  State<RelationshipEditorDialog> createState() =>
      _RelationshipEditorDialogState();
}

class _RelationshipEditorDialogState extends State<RelationshipEditorDialog> {
  final _formKey = GlobalKey<FormState>();
  late String _level;
  late final TextEditingController _score;
  late final TextEditingController _status;
  late final TextEditingController _context;
  late final TextEditingController _reason;

  @override
  void initState() {
    super.initState();
    _level = widget.current.level;
    _score = TextEditingController(
      text: widget.current.affectionScore.toString(),
    );
    _status = TextEditingController(text: widget.current.status);
    _context = TextEditingController(text: widget.current.context);
    _reason = TextEditingController();
  }

  @override
  void dispose() {
    _score.dispose();
    _status.dispose();
    _context.dispose();
    _reason.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Cập nhật quan hệ'),
      content: SizedBox(
        width: 520,
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                DropdownButtonFormField<String>(
                  initialValue: _level,
                  decoration: const InputDecoration(labelText: 'Cấp quan hệ'),
                  items: List<DropdownMenuItem<String>>.generate(
                    7,
                    (index) => DropdownMenuItem<String>(
                      value: 'l$index',
                      child: Text('L$index'),
                    ),
                  ),
                  onChanged: (value) => setState(() => _level = value ?? _level),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _score,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Affection score (-100 đến 100)',
                  ),
                  validator: (value) {
                    final score = int.tryParse(value ?? '');
                    if (score == null || score < -100 || score > 100) {
                      return 'Điểm phải nằm trong khoảng -100 đến 100.';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _status,
                  decoration: const InputDecoration(labelText: 'Trạng thái'),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _context,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Ngữ cảnh quan hệ'),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _reason,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Lý do thay đổi',
                  ),
                  validator: (value) => value == null || value.trim().isEmpty
                      ? 'Cần ghi lý do để lưu lịch sử.'
                      : null,
                ),
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

  void _submit() {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    Navigator.of(context).pop(<String, Object?>{
      'level': _level,
      'affection_score': int.parse(_score.text),
      'status': _nullable(_status.text),
      'context': _nullable(_context.text),
      'reason': _reason.text.trim(),
    });
  }

  String? _nullable(String value) {
    final normalized = value.trim();
    return normalized.isEmpty ? null : normalized;
  }
}

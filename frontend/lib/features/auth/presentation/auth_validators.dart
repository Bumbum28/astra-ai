abstract final class AuthValidators {
  static final RegExp _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
  static final RegExp _usernamePattern = RegExp(r'^[a-zA-Z0-9_.-]+$');

  static String? email(String? value) {
    final normalized = value?.trim() ?? '';
    if (normalized.isEmpty) {
      return 'Hãy nhập email.';
    }
    if (!_emailPattern.hasMatch(normalized)) {
      return 'Email không đúng định dạng.';
    }
    return null;
  }

  static String? username(String? value) {
    final normalized = value?.trim() ?? '';
    if (normalized.length < 3) {
      return 'Tên người dùng cần ít nhất 3 ký tự.';
    }
    if (!_usernamePattern.hasMatch(normalized)) {
      return 'Chỉ dùng chữ, số, dấu chấm, gạch ngang hoặc gạch dưới.';
    }
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Hãy nhập mật khẩu.';
    }
    if (value.length < 8) {
      return 'Mật khẩu cần ít nhất 8 ký tự.';
    }
    return null;
  }

  static String? confirmPassword(String? value, String password) {
    if (value != password) {
      return 'Mật khẩu xác nhận không khớp.';
    }
    return null;
  }
}

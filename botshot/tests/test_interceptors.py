import pytest
import mock
from botshot.core.interceptors import BotshotVersionDialogInterceptor, AdminDialogInterceptor


class TestInterceptors:

    def test_botshot_version(self):
        interceptor = BotshotVersionDialogInterceptor()
        dialog = mock.Mock()
        dialog.message.text = "/areyoubotshot"
        assert interceptor.intercept(dialog)
        dialog.message.text = "/areyoubot"
        assert not interceptor.intercept(dialog)

    def test_admin_dialog(self):
        interceptor = AdminDialogInterceptor()
        dialog = mock.Mock()
        dialog.message.text = "/admin"
        assert interceptor.intercept(dialog)

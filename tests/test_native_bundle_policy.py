import unittest
from scripts.native_bundle_policy import needed, QT_DLLS


class NativeBundlePolicyTests(unittest.TestCase):
    def entry(self, name):
        return (name, 'source', 'BINARY')

    def test_browser_and_unused_qt_graphics_are_not_packaged(self):
        for name in ['PySide6/Qt6WebEngineCore.dll', 'PySide6\\Qt6Quick.dll', 'PySide6/Qt6Pdf.dll', 'PySide6/Qt6Charts.dll', 'PySide6/opengl32sw.dll', 'PySide6/qml/QtQuick/plugin.dll', 'PySide6/resources/qtwebengine_resources.pak']:
            self.assertFalse(needed(self.entry(name)), name)

    def test_native_runtime_and_platform_plugin_are_preserved(self):
        for name in [*[f'PySide6/{dll}' for dll in QT_DLLS], 'PySide6/QtWidgets.pyd', 'PySide6/pyside6qml.abi3.dll', 'PySide6/plugins/platforms/qwindows.dll', 'PySide6/plugins/styles/qmodernwindowsstyle.dll', 'python310.dll', 'VCRUNTIME140.dll', 'web/native-bundle.js']:
            self.assertTrue(needed(self.entry(name)), name)
        self.assertFalse(needed(self.entry('PySide6/plugins/platforms/qwebgl.dll')))


if __name__ == '__main__': unittest.main()

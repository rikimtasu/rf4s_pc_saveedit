"""Keep only runtime dependencies used by native Widgets and QJSEngine."""

# Audited PE import chains: Widgets -> Gui -> Core; Qml -> Network -> Core.
# QJSEngine interprets save algorithms; no QML scene or Quick renderer is used.
QT_DLLS = {'qt6core.dll', 'qt6gui.dll', 'qt6widgets.dll', 'qt6qml.dll', 'qt6network.dll'}


def needed(entry):
    name = entry[0].replace('\\', '/').lower()
    if name.startswith(('pyside6/qml/', 'pyside6/translations/', 'pyside6/resources/')):
        return False
    if name.startswith('pyside6/plugins/'):
        return name == 'pyside6/plugins/platforms/qwindows.dll' or name.startswith('pyside6/plugins/styles/')
    basename = name.rsplit('/', 1)[-1]
    if name.startswith('pyside6/') and basename.startswith('qt') and basename.endswith('.dll'):
        return basename in QT_DLLS
    if basename == 'opengl32sw.dll':
        return False  # These native controls use raster painting, not OpenGL.
    return True

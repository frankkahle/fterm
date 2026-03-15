#include "mainwindow.h"
#include "settings.h"
#include "splashscreen.h"
#include "thememanager.h"
#include "version.h"

#include <QApplication>
#include <qtermwidget5/qtermwidget.h>
#include <QCommandLineParser>
#include <QDir>
#include <QIcon>
#include <QTimer>

int main(int argc, char *argv[])
{
    // High-DPI support
    QApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);

    QApplication app(argc, argv);
    app.setApplicationName("SOSterm");
    app.setOrganizationName("SOS Tech Services");
    app.setApplicationVersion(SOSTERM_VERSION);

    // Force Fusion style to prevent system dark theme bleed
    app.setStyle("Fusion");

    // App icon
    QIcon appIcon;
    if (QFile::exists(":/resources/SOSterm.svg"))
        appIcon = QIcon(":/resources/SOSterm.svg");
    else if (QFile::exists("/opt/SOSterm/resources/SOSterm.svg"))
        appIcon = QIcon("/opt/SOSterm/resources/SOSterm.svg");
    app.setWindowIcon(appIcon);

    // Command line
    QCommandLineParser parser;
    parser.setApplicationDescription("SOSterm - Terminal Emulator");
    parser.addHelpOption();
    parser.addVersionOption();

    QCommandLineOption shellOption({"e", "execute"}, "Shell to execute", "shell");
    QCommandLineOption dirOption({"d", "directory"}, "Starting directory", "path");
    QCommandLineOption newOption({"n", "new"}, "Start fresh, ignore saved session");
    parser.addOption(shellOption);
    parser.addOption(dirOption);
    parser.addOption(newOption);
    parser.process(app);

    // Register custom color schemes
    ThemeManager::registerColorSchemes();

    // Splash screen
    SplashScreen splash(SOSTERM_VERSION);
    splash.show();
    splash.setStatus("Loading settings...");
    app.processEvents();

    // Settings
    Settings settings;
    splash.setStatus("Initializing...");
    app.processEvents();

    // Main window
    MainWindow window(&settings, SOSTERM_VERSION);

    // Restore session unless --new
    bool restored = false;
    if (!parser.isSet(newOption)) {
        splash.setStatus("Restoring session...");
        app.processEvents();
        restored = window.restoreSession();
    }

    // Ensure at least one tab
    QString shell = parser.value(shellOption);
    QString cwd = parser.value(dirOption);
    if (!restored || window.tabManager()->count() == 0)
        window.ensureOneTab(shell, cwd);

    // Show main window after splash minimum display
    splash.setStatus("Ready");
    QTimer::singleShot(2500, &app, [&]() {
        window.show();
        splash.close();
        if (auto *term = window.tabManager()->currentTerminal())
            term->setFocus();
    });

    return app.exec();
}

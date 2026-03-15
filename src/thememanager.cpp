#include "thememanager.h"

#include <QApplication>
#include <QDir>
#include <qtermwidget5/qtermwidget.h>

QStringList ThemeManager::themeNames()
{
    return {"Dark", "Light", "Solarized Dark", "Dracula", "Nord", "Gruvbox", "Monokai"};
}

ThemeInfo ThemeManager::theme(const QString &name)
{
    ThemeInfo t;
    t.name = name;

    if (name == "Light") {
        t.colorSchemeName = "SOStermLight";
        t.terminalBg = "#FFFFFF"; t.terminalFg = "#000000";
        t.cursorColor = "#000000";
        t.selectionBg = "#ADD6FF"; t.selectionFg = "#000000";
        t.tabBarBg = "#E8E8E8";
        t.statusBarBg = "#007ACC"; t.statusBarFg = "#FFFFFF";
        t.menuBg = "#F0F0F0"; t.menuFg = "#000000";
        t.borderColor = "#CCCCCC";
    } else if (name == "Solarized Dark") {
        t.colorSchemeName = "SOStermSolarizedDark";
        t.terminalBg = "#002B36"; t.terminalFg = "#839496";
        t.cursorColor = "#839496";
        t.selectionBg = "#073642"; t.selectionFg = "#93A1A1";
        t.tabBarBg = "#073642";
        t.statusBarBg = "#073642"; t.statusBarFg = "#839496";
        t.menuBg = "#002B36"; t.menuFg = "#839496";
        t.borderColor = "#073642";
    } else if (name == "Dracula") {
        t.colorSchemeName = "SOStermDracula";
        t.terminalBg = "#282A36"; t.terminalFg = "#F8F8F2";
        t.cursorColor = "#F8F8F2";
        t.selectionBg = "#44475A"; t.selectionFg = "#F8F8F2";
        t.tabBarBg = "#21222C";
        t.statusBarBg = "#44475A"; t.statusBarFg = "#F8F8F2";
        t.menuBg = "#282A36"; t.menuFg = "#F8F8F2";
        t.borderColor = "#44475A";
    } else if (name == "Nord") {
        t.colorSchemeName = "SOStermNord";
        t.terminalBg = "#2E3440"; t.terminalFg = "#D8DEE9";
        t.cursorColor = "#D8DEE9";
        t.selectionBg = "#434C5E"; t.selectionFg = "#ECEFF4";
        t.tabBarBg = "#3B4252";
        t.statusBarBg = "#434C5E"; t.statusBarFg = "#ECEFF4";
        t.menuBg = "#2E3440"; t.menuFg = "#D8DEE9";
        t.borderColor = "#4C566A";
    } else if (name == "Gruvbox") {
        t.colorSchemeName = "SOStermGruvbox";
        t.terminalBg = "#282828"; t.terminalFg = "#EBDBB2";
        t.cursorColor = "#EBDBB2";
        t.selectionBg = "#504945"; t.selectionFg = "#FBF1C7";
        t.tabBarBg = "#1D2021";
        t.statusBarBg = "#504945"; t.statusBarFg = "#EBDBB2";
        t.menuBg = "#282828"; t.menuFg = "#EBDBB2";
        t.borderColor = "#504945";
    } else if (name == "Monokai") {
        t.colorSchemeName = "SOStermMonokai";
        t.terminalBg = "#272822"; t.terminalFg = "#F8F8F2";
        t.cursorColor = "#F8F8F0";
        t.selectionBg = "#49483E"; t.selectionFg = "#F8F8F2";
        t.tabBarBg = "#1E1F1C";
        t.statusBarBg = "#49483E"; t.statusBarFg = "#F8F8F2";
        t.menuBg = "#272822"; t.menuFg = "#F8F8F2";
        t.borderColor = "#49483E";
    } else {
        // Dark (default)
        t.colorSchemeName = "SOStermDark";
        t.terminalBg = "#1E1E1E"; t.terminalFg = "#D4D4D4";
        t.cursorColor = "#AEAFAD";
        t.selectionBg = "#264F78"; t.selectionFg = "#FFFFFF";
        t.tabBarBg = "#252526";
        t.statusBarBg = "#007ACC"; t.statusBarFg = "#FFFFFF";
        t.menuBg = "#2D2D2D"; t.menuFg = "#D4D4D4";
        t.borderColor = "#404040";
    }

    return t;
}

QString ThemeManager::appStyleSheet(const ThemeInfo &t)
{
    return QStringLiteral(
        "QMainWindow { background-color: %1; }"
        "QMenuBar { background-color: %2; color: %3; border-bottom: 1px solid %4; }"
        "QMenuBar::item:selected { background-color: %5; color: %6; }"
        "QMenu { background-color: %2; color: %3; border: 1px solid %4; }"
        "QMenu::item:selected { background-color: %5; color: %6; }"
        "QMenu::separator { height: 1px; background-color: %4; }"
        "QTabWidget::pane { border: 1px solid %4; }"
        "QTabBar { background-color: %7; }"
        "QTabBar::tab { background-color: %7; color: %3; padding: 6px 14px;"
        "  border: 1px solid %4; border-bottom: none; margin-right: 1px; }"
        "QTabBar::tab:selected { background-color: %1; color: %8; }"
        "QTabBar::tab:hover { background-color: %5; }"
        "QStatusBar { background-color: %9; color: %10; border-top: 1px solid %4; }"
        "QStatusBar QLabel { color: %10; padding: 0 8px; }"
        "QToolBar { background-color: %7; border-bottom: 1px solid %4; spacing: 2px; padding: 2px; }"
        "QToolButton { background-color: transparent; border: 1px solid transparent;"
        "  border-radius: 3px; padding: 3px; color: %3; }"
        "QToolButton:hover { background-color: %5; border: 1px solid %4; }"
        "QDialog { background-color: %2; color: %3; }"
        "QLabel { color: %3; }"
        "QLineEdit, QTextEdit, QPlainTextEdit { background-color: %1; color: %8;"
        "  border: 1px solid %4; padding: 3px; }"
        "QCheckBox { color: %3; }"
        "QPushButton { background-color: %7; color: %3; border: 1px solid %4;"
        "  padding: 5px 15px; border-radius: 3px; }"
        "QPushButton:hover { background-color: %5; color: %6; }"
        "QComboBox { background-color: %1; color: %8; border: 1px solid %4; padding: 3px; }"
        "QComboBox QAbstractItemView { background-color: %2; color: %3;"
        "  selection-background-color: %5; selection-color: %6; }"
        "QSpinBox { background-color: %1; color: %8; border: 1px solid %4; }"
        "QGroupBox { color: %3; border: 1px solid %4; margin-top: 6px; padding-top: 10px; }"
        "QGroupBox::title { subcontrol-origin: margin; padding: 0 5px; }"
        "QScrollBar:vertical { background-color: %7; width: 14px; }"
        "QScrollBar::handle:vertical { background-color: %4; min-height: 20px;"
        "  border-radius: 3px; margin: 2px; }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        "QTreeWidget { background-color: %1; color: %8; border: 1px solid %4; outline: none; }"
        "QTreeWidget::item { padding: 3px 0; }"
        "QTreeWidget::item:selected { background-color: %5; color: %6; }"
        "QTreeWidget::item:hover { background-color: %5; }"
        "QTreeWidget::branch { background-color: %1; }"
        "QSplitter::handle { background-color: %4; width: 1px; }"
        "QSplitter::handle:hover { background-color: %5; }"
        "QFontComboBox { background-color: %1; color: %8; border: 1px solid %4; padding: 3px; }"
        "QFontComboBox QAbstractItemView { background-color: %2; color: %3;"
        "  selection-background-color: %5; selection-color: %6; }"
    ).arg(t.terminalBg, t.menuBg, t.menuFg, t.borderColor,
          t.selectionBg, t.selectionFg, t.tabBarBg, t.terminalFg)
     .arg(t.statusBarBg, t.statusBarFg);
}

void ThemeManager::registerColorSchemes()
{
    // Try install path first, then source tree
    QStringList searchPaths = {
        "/opt/SOSterm/colorschemes",
        QApplication::applicationDirPath() + "/../colorschemes",
        QApplication::applicationDirPath() + "/colorschemes"
    };

    for (const auto &path : searchPaths) {
        if (QDir(path).exists()) {
            QTermWidget::addCustomColorSchemeDir(path);
            return;
        }
    }
}

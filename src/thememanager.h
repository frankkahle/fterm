#ifndef SOSTERM_THEMEMANAGER_H
#define SOSTERM_THEMEMANAGER_H

#include <QString>
#include <QStringList>

struct ThemeInfo {
    QString name;
    QString colorSchemeName;
    // Terminal
    QString terminalBg, terminalFg;
    QString cursorColor;
    QString selectionBg, selectionFg;
    // UI chrome
    QString tabBarBg;
    QString statusBarBg, statusBarFg;
    QString menuBg, menuFg;
    QString borderColor;
};

class ThemeManager
{
public:
    static QStringList themeNames();
    static ThemeInfo theme(const QString &name);
    static QString appStyleSheet(const ThemeInfo &t);
    static void registerColorSchemes();
};

#endif // SOSTERM_THEMEMANAGER_H

#ifndef SOSTERM_SESSIONTABMANAGER_H
#define SOSTERM_SESSIONTABMANAGER_H

#include <QTabWidget>
#include <QJsonObject>
#include <QJsonArray>

#include "settings.h"
#include "sshsessionstore.h"

class QTermWidget;

class SessionTabManager : public QTabWidget
{
    Q_OBJECT

public:
    explicit SessionTabManager(Settings *settings, QWidget *parent = nullptr);

    QTermWidget *newTab(const QString &shell = QString(), const QString &cwd = QString());
    QTermWidget *newSSHTab(const SSHSession &session, const QString &tabTitle = QString());
    bool closeTab(int index = -1);
    void closeAllTabs();
    void closeOtherTabs(int index);

    QTermWidget *currentTerminal() const;

    QJsonObject getSessionData() const;
    void restoreSessionData(const QJsonObject &data);
    void setSSHStore(SSHSessionStore *store);

signals:
    void currentTerminalChanged(QTermWidget *term);
    void tabCountChanged(int count);
    void terminalTitleChanged(const QString &title);

private slots:
    void onCurrentChanged(int index);
    void onTerminalFinished();
    void onTitleChanged();
    void showTabContextMenu(const QPoint &pos);

private:
    void configureTerminal(QTermWidget *term);
    QTermWidget *createTerminal();

    Settings *m_settings;
    SSHSessionStore *m_sshStore = nullptr;
    int m_tabCounter = 0;
};

#endif // SOSTERM_SESSIONTABMANAGER_H

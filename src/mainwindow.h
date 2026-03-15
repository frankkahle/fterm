#ifndef SOSTERM_MAINWINDOW_H
#define SOSTERM_MAINWINDOW_H

#include <QMainWindow>
#include <QLabel>
#include <QSplitter>
#include <QTimer>

#include "sessionmanager.h"
#include "sessiontabmanager.h"
#include "settings.h"
#include "sshsessionstore.h"
#include "sshsidebar.h"
#include "updatechecker.h"

class QTermWidget;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(Settings *settings, const QString &version,
                        QWidget *parent = nullptr);

    SessionTabManager *tabManager() const { return m_tabManager; }
    bool restoreSession();
    void ensureOneTab(const QString &shell = QString(), const QString &cwd = QString());

protected:
    void closeEvent(QCloseEvent *event) override;
    bool eventFilter(QObject *obj, QEvent *event) override;

private slots:
    void newTab();
    void closeTab();
    void onCopy();
    void onPaste();
    void onFind();
    void zoomIn();
    void zoomOut();
    void zoomReset();
    void nextTab();
    void prevTab();
    void toggleFullscreen();
    void toggleSSHPanel();
    void showSSHConnectDialog();
    void showPreferences();
    void showAbout();
    void checkForUpdates();
    void importSSHConfig();
    void importRemmina();

    void onTerminalChanged(QTermWidget *term);
    void onTabCountChanged(int count);
    void onTitleChanged(const QString &title);
    void onSettingsChanged(const QString &key, const QVariant &value);
    void onSSHConnect(const SSHSession &session);
    void onQuickConnect(const QString &input);
    void onUpdateAvailable(const QString &version, const QString &url, const QString &changelog);
    void updateStatusBar();

private:
    void setupCentralWidget();
    void createActions();
    void createMenus();
    void createToolbar();
    void createStatusBar();
    void applyTheme();
    void applyThemeToTerminals();
    void restoreGeometry();
    void saveGeometry();

    // SSH dialog handlers
    void onEditSession(const SSHSession &session);
    void onEditGroup(const SSHGroup &group);
    void onDeleteSession(const SSHSession &session);
    void onDeleteGroup(const SSHGroup &group);
    void onNewSession();
    void onNewGroup();

    Settings *m_settings;
    QString m_version;

    SessionTabManager *m_tabManager;
    SSHSessionStore *m_sshStore;
    SSHSidebarPanel *m_sshSidebar;
    SessionManager m_sessionManager;
    UpdateChecker *m_updateChecker;

    QSplitter *m_splitter;
    QTimer *m_statusTimer;

    // Status bar labels
    QLabel *m_sshInfoLabel;
    QLabel *m_dimsLabel;
    QLabel *m_shellLabel;
    QLabel *m_cwdLabel;

    // Actions
    QAction *m_sshPanelAction;

    // Track selection for Ctrl+C awareness
    bool m_hasSelection = false;
};

#endif // SOSTERM_MAINWINDOW_H

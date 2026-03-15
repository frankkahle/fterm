#include "mainwindow.h"
#include "preferencesdialog.h"
#include "sshdialogs.h"
#include "thememanager.h"
#include "version.h"

#include <QAction>
#include <QApplication>
#include <QCloseEvent>
#include <QContextMenuEvent>
#include <QDesktopServices>
#include <QFileInfo>
#include <QKeyEvent>
#include <QMenuBar>
#include <QMessageBox>
#include <QProcess>
#include <QScreen>
#include <QStatusBar>
#include <QToolBar>
#include <QUrl>
#include <QVBoxLayout>
#include <qtermwidget5/qtermwidget.h>

MainWindow::MainWindow(Settings *settings, const QString &version, QWidget *parent)
    : QMainWindow(parent)
    , m_settings(settings)
    , m_version(version)
{
    setWindowTitle("SOSterm");
    resize(900, 600);

    m_sshStore = new SSHSessionStore(QString(), this);
    m_tabManager = new SessionTabManager(m_settings, this);
    m_tabManager->setSSHStore(m_sshStore);
    m_sshSidebar = new SSHSidebarPanel(m_sshStore, this);
    m_updateChecker = new UpdateChecker(m_settings, m_version, this);

    setupCentralWidget();
    createActions();
    createMenus();
    createToolbar();
    createStatusBar();
    applyTheme();

    // Connections
    connect(m_tabManager, &SessionTabManager::currentTerminalChanged,
            this, &MainWindow::onTerminalChanged);
    connect(m_tabManager, &SessionTabManager::tabCountChanged,
            this, &MainWindow::onTabCountChanged);
    connect(m_tabManager, &SessionTabManager::terminalTitleChanged,
            this, &MainWindow::onTitleChanged);
    connect(m_settings, &Settings::settingsChanged,
            this, &MainWindow::onSettingsChanged);

    // SSH sidebar signals
    connect(m_sshSidebar, &SSHSidebarPanel::connectRequested,
            this, &MainWindow::onSSHConnect);
    connect(m_sshSidebar, &SSHSidebarPanel::quickConnectRequested,
            this, &MainWindow::onQuickConnect);
    connect(m_sshSidebar, &SSHSidebarPanel::editSessionRequested,
            this, &MainWindow::onEditSession);
    connect(m_sshSidebar, &SSHSidebarPanel::editGroupRequested,
            this, &MainWindow::onEditGroup);
    connect(m_sshSidebar, &SSHSidebarPanel::deleteSessionRequested,
            this, &MainWindow::onDeleteSession);
    connect(m_sshSidebar, &SSHSidebarPanel::deleteGroupRequested,
            this, &MainWindow::onDeleteGroup);
    connect(m_sshSidebar, &SSHSidebarPanel::newSessionRequested,
            this, &MainWindow::onNewSession);
    connect(m_sshSidebar, &SSHSidebarPanel::newGroupRequested,
            this, &MainWindow::onNewGroup);

    // Update checker
    connect(m_updateChecker, &UpdateChecker::updateAvailable,
            this, &MainWindow::onUpdateAvailable);

    restoreGeometry();

    // Status bar update timer
    m_statusTimer = new QTimer(this);
    connect(m_statusTimer, &QTimer::timeout, this, &MainWindow::updateStatusBar);
    m_statusTimer->start(2000);

    // Auto-check for updates after 3 seconds
    QTimer::singleShot(3000, m_updateChecker, &UpdateChecker::autoCheck);
}

void MainWindow::setupCentralWidget()
{
    m_splitter = new QSplitter(Qt::Horizontal, this);

    m_sshSidebar->setMinimumWidth(180);
    m_sshSidebar->setMaximumWidth(350);
    m_splitter->addWidget(m_sshSidebar);
    m_splitter->addWidget(m_tabManager);
    m_splitter->setSizes({220, 680});

    setCentralWidget(m_splitter);
}

void MainWindow::createActions()
{
    // SSH Panel toggle (needed for menu)
    m_sshPanelAction = new QAction("SSH Sessions Panel", this);
    m_sshPanelAction->setShortcut(QKeySequence("Ctrl+Shift+P"));
    m_sshPanelAction->setCheckable(true);
    m_sshPanelAction->setChecked(true);
    connect(m_sshPanelAction, &QAction::toggled, this, &MainWindow::toggleSSHPanel);
}

void MainWindow::createMenus()
{
    // File
    auto *fileMenu = menuBar()->addMenu("&File");
    fileMenu->addAction("New Tab", this, &MainWindow::newTab,
                        QKeySequence("Ctrl+Shift+T"));
    fileMenu->addAction("Close Tab", this, &MainWindow::closeTab,
                        QKeySequence("Ctrl+Shift+W"));
    fileMenu->addSeparator();
    fileMenu->addAction("SSH Connect...", this, &MainWindow::showSSHConnectDialog,
                        QKeySequence("Ctrl+Shift+S"));
    fileMenu->addAction("Import SSH Config...", this, &MainWindow::importSSHConfig);
    fileMenu->addAction("Import from Remmina...", this, &MainWindow::importRemmina);
    fileMenu->addSeparator();
    fileMenu->addAction("Exit", this, &QWidget::close, QKeySequence("Alt+F4"));

    // Edit
    auto *editMenu = menuBar()->addMenu("&Edit");
    editMenu->addAction("Copy", this, &MainWindow::onCopy,
                        QKeySequence("Ctrl+Shift+C"));
    editMenu->addAction("Paste", this, &MainWindow::onPaste,
                        QKeySequence("Ctrl+Shift+V"));
    editMenu->addSeparator();
    editMenu->addAction("Find", this, &MainWindow::onFind,
                        QKeySequence("Ctrl+Shift+F"));
    editMenu->addSeparator();
    editMenu->addAction("Clear", this, [this]() {
        if (auto *t = m_tabManager->currentTerminal())
            t->clear();
    });

    // View
    auto *viewMenu = menuBar()->addMenu("&View");
    viewMenu->addAction(m_sshPanelAction);
    viewMenu->addSeparator();
    viewMenu->addAction("Zoom In", this, &MainWindow::zoomIn,
                        QKeySequence("Ctrl+Shift+="));
    viewMenu->addAction("Zoom Out", this, &MainWindow::zoomOut,
                        QKeySequence("Ctrl+Shift+-"));
    viewMenu->addAction("Reset Zoom", this, &MainWindow::zoomReset,
                        QKeySequence("Ctrl+Shift+0"));
    viewMenu->addSeparator();
    auto *fullscreenAction = viewMenu->addAction("Full Screen", this,
                                                  &MainWindow::toggleFullscreen,
                                                  QKeySequence("F11"));
    fullscreenAction->setCheckable(true);

    // Tabs
    auto *tabsMenu = menuBar()->addMenu("&Tabs");
    tabsMenu->addAction("Next Tab", this, &MainWindow::nextTab,
                        QKeySequence("Ctrl+Tab"));
    tabsMenu->addAction("Previous Tab", this, &MainWindow::prevTab,
                        QKeySequence("Ctrl+Shift+Tab"));

    // Tools
    auto *toolsMenu = menuBar()->addMenu("T&ools");
    toolsMenu->addAction("Preferences...", this, &MainWindow::showPreferences);

    // Help
    auto *helpMenu = menuBar()->addMenu("&Help");
    helpMenu->addAction("Check for Updates...", this, &MainWindow::checkForUpdates);
    helpMenu->addSeparator();
    helpMenu->addAction("About SOSterm", this, &MainWindow::showAbout);
}

void MainWindow::createToolbar()
{
    auto *toolbar = addToolBar("Main");
    toolbar->setMovable(false);
    toolbar->setIconSize(QSize(16, 16));

    toolbar->addAction("New Tab", this, &MainWindow::newTab);
    toolbar->addAction("SSH Connect", this, &MainWindow::showSSHConnectDialog);
    toolbar->addSeparator();
    toolbar->addAction("Copy", this, &MainWindow::onCopy);
    toolbar->addAction("Paste", this, &MainWindow::onPaste);
    toolbar->addSeparator();
    toolbar->addAction("Zoom In", this, &MainWindow::zoomIn);
    toolbar->addAction("Zoom Out", this, &MainWindow::zoomOut);
}

void MainWindow::createStatusBar()
{
    m_sshInfoLabel = new QLabel;
    m_sshInfoLabel->setMinimumWidth(100);
    m_dimsLabel = new QLabel;
    m_dimsLabel->setMinimumWidth(80);
    m_shellLabel = new QLabel;
    m_shellLabel->setMinimumWidth(80);
    m_cwdLabel = new QLabel;
    m_cwdLabel->setMinimumWidth(200);

    statusBar()->addPermanentWidget(m_sshInfoLabel);
    statusBar()->addPermanentWidget(m_dimsLabel);
    statusBar()->addPermanentWidget(m_shellLabel);
    statusBar()->addPermanentWidget(m_cwdLabel);
}

void MainWindow::applyTheme()
{
    QString themeName = m_settings->get("theme", "Dark").toString();
    ThemeInfo ti = ThemeManager::theme(themeName);
    setStyleSheet(ThemeManager::appStyleSheet(ti));
    applyThemeToTerminals();
}

void MainWindow::applyThemeToTerminals()
{
    QString themeName = m_settings->get("theme", "Dark").toString();
    ThemeInfo ti = ThemeManager::theme(themeName);
    for (int i = 0; i < m_tabManager->count(); ++i) {
        auto *term = qobject_cast<QTermWidget *>(m_tabManager->widget(i));
        if (term)
            term->setColorScheme(ti.colorSchemeName);
    }
}

void MainWindow::restoreGeometry()
{
    QString geo = m_settings->get("window_geometry").toString();
    QString state = m_settings->get("window_state").toString();

    if (!geo.isEmpty())
        QMainWindow::restoreGeometry(QByteArray::fromBase64(geo.toUtf8()));
    if (!state.isEmpty())
        QMainWindow::restoreState(QByteArray::fromBase64(state.toUtf8()));

    // Ensure visible on a current screen
    if (auto *screen = QApplication::primaryScreen()) {
        QRect avail = screen->availableGeometry();
        QRect geo = geometry();
        if (!avail.intersects(geo)) {
            move(avail.center() - QPoint(width() / 2, height() / 2));
        }
    }
}

void MainWindow::saveGeometry()
{
    m_settings->set("window_geometry",
                    QString::fromUtf8(QMainWindow::saveGeometry().toBase64()));
    m_settings->set("window_state",
                    QString::fromUtf8(QMainWindow::saveState().toBase64()));
}

// --- Slots ---

void MainWindow::newTab()
{
    m_tabManager->newTab();
}

void MainWindow::closeTab()
{
    m_tabManager->closeTab();
}

void MainWindow::onCopy()
{
    if (auto *t = m_tabManager->currentTerminal())
        t->copyClipboard();
}

void MainWindow::onPaste()
{
    if (auto *t = m_tabManager->currentTerminal())
        t->pasteClipboard();
}

void MainWindow::onFind()
{
    if (auto *t = m_tabManager->currentTerminal())
        t->toggleShowSearchBar();
}

void MainWindow::zoomIn()
{
    if (auto *t = m_tabManager->currentTerminal()) {
        t->zoomIn();
        int zoom = m_settings->get("zoom_level", 0).toInt() + 1;
        m_settings->set("zoom_level", zoom);
    }
}

void MainWindow::zoomOut()
{
    if (auto *t = m_tabManager->currentTerminal()) {
        t->zoomOut();
        int zoom = m_settings->get("zoom_level", 0).toInt() - 1;
        m_settings->set("zoom_level", zoom);
    }
}

void MainWindow::zoomReset()
{
    // Reset all terminals to base font size
    int currentZoom = m_settings->get("zoom_level", 0).toInt();
    for (int i = 0; i < m_tabManager->count(); ++i) {
        auto *t = qobject_cast<QTermWidget *>(m_tabManager->widget(i));
        if (!t) continue;
        if (currentZoom > 0) {
            for (int j = 0; j < currentZoom; ++j) t->zoomOut();
        } else {
            for (int j = 0; j > currentZoom; --j) t->zoomIn();
        }
    }
    m_settings->set("zoom_level", 0);
}

void MainWindow::nextTab()
{
    int idx = m_tabManager->currentIndex() + 1;
    if (idx >= m_tabManager->count()) idx = 0;
    m_tabManager->setCurrentIndex(idx);
}

void MainWindow::prevTab()
{
    int idx = m_tabManager->currentIndex() - 1;
    if (idx < 0) idx = m_tabManager->count() - 1;
    m_tabManager->setCurrentIndex(idx);
}

void MainWindow::toggleFullscreen()
{
    if (isFullScreen())
        showNormal();
    else
        showFullScreen();
}

void MainWindow::toggleSSHPanel()
{
    m_sshSidebar->setVisible(m_sshPanelAction->isChecked());
}

void MainWindow::showSSHConnectDialog()
{
    SSHSessionDialog dlg(m_sshStore, SSHSession(), this);
    if (dlg.exec() == QDialog::Accepted) {
        SSHSession s = dlg.result();
        m_sshStore->addSession(s);
        m_sshSidebar->refresh();
        onSSHConnect(s);
    }
}

void MainWindow::showPreferences()
{
    PreferencesDialog dlg(m_settings, this);
    dlg.exec();
}

void MainWindow::showAbout()
{
    QMessageBox::about(this, "About SOSterm",
        QStringLiteral(
            "<h2>SOSterm v%1</h2>"
            "<p>A terminal emulator by S.O.S. Tech Services</p>"
            "<p><a href=\"https://sos-tech.ca\">sos-tech.ca</a></p>"
        ).arg(m_version));
}

void MainWindow::checkForUpdates()
{
    m_updateChecker->check(false);
    // One-shot connection for manual check feedback
    auto *conn = new QMetaObject::Connection;
    *conn = connect(m_updateChecker, &UpdateChecker::checkFinished,
            this, [this, conn](bool hadUpdate) {
        disconnect(*conn);
        delete conn;
        if (!hadUpdate)
            QMessageBox::information(this, "Update Check",
                                     "You are running the latest version.");
    });
}

void MainWindow::importSSHConfig()
{
    auto candidates = m_sshStore->importSSHConfig();
    if (candidates.isEmpty()) {
        QMessageBox::information(this, "Import",
                                 "No new sessions found in ~/.ssh/config.");
        return;
    }
    SSHImportDialog dlg(candidates, "Select sessions to import from ~/.ssh/config:", this);
    if (dlg.exec() == QDialog::Accepted) {
        for (const auto &s : dlg.selectedSessions())
            m_sshStore->addSession(s);
        m_sshSidebar->refresh();
    }
}

void MainWindow::importRemmina()
{
    auto candidates = m_sshStore->importRemmina();
    if (candidates.isEmpty()) {
        QMessageBox::information(this, "Import",
                                 "No new SSH sessions found in Remmina.");
        return;
    }
    SSHImportDialog dlg(candidates, "Select SSH sessions to import from Remmina:", this);
    if (dlg.exec() == QDialog::Accepted) {
        for (const auto &s : dlg.selectedSessions())
            m_sshStore->addSession(s);
        m_sshSidebar->refresh();
    }
}

void MainWindow::onTerminalChanged(QTermWidget *term)
{
    m_hasSelection = false;
    if (term) {
        // Track selection for Ctrl+C awareness
        connect(term, &QTermWidget::copyAvailable, this, [this](bool available) {
            m_hasSelection = available;
        }, Qt::UniqueConnection);

        // Install event filter for Ctrl+C/V and right-click context menu
        term->installEventFilter(this);

        term->setFocus();
    }
    updateStatusBar();
}

void MainWindow::onTabCountChanged(int count)
{
    setWindowTitle(count > 1
        ? QStringLiteral("SOSterm (%1 tabs)").arg(count)
        : "SOSterm");
}

void MainWindow::onTitleChanged(const QString &title)
{
    if (!title.isEmpty())
        setWindowTitle(QStringLiteral("SOSterm - %1").arg(title));
}

void MainWindow::onSettingsChanged(const QString &key, const QVariant &)
{
    if (key == "theme") {
        applyTheme();
    } else if (key == "font_family" || key == "font_size" || key == "cursor_style"
               || key == "cursor_blink" || key == "scrollback_lines"
               || key == "terminal_padding") {
        // Reconfigure all terminals
        for (int i = 0; i < m_tabManager->count(); ++i) {
            auto *t = qobject_cast<QTermWidget *>(m_tabManager->widget(i));
            if (!t) continue;

            QFont font(m_settings->get("font_family", "Monospace").toString());
            font.setPointSize(m_settings->get("font_size", 11).toInt());
            t->setTerminalFont(font);
            t->setHistorySize(m_settings->get("scrollback_lines", 10000).toInt());
            t->setMargin(m_settings->get("terminal_padding", 4).toInt());

            QString cursorStyle = m_settings->get("cursor_style", "block").toString();
            if (cursorStyle == "underline")
                t->setKeyboardCursorShape(Konsole::Emulation::KeyboardCursorShape::UnderlineCursor);
            else if (cursorStyle == "bar")
                t->setKeyboardCursorShape(Konsole::Emulation::KeyboardCursorShape::IBeamCursor);
            else
                t->setKeyboardCursorShape(Konsole::Emulation::KeyboardCursorShape::BlockCursor);

            t->setBlinkingCursor(m_settings->get("cursor_blink", true).toBool());
        }
    }
}

void MainWindow::onSSHConnect(const SSHSession &session)
{
    m_tabManager->newSSHTab(session);
}

void MainWindow::onQuickConnect(const QString &input)
{
    // Parse user@host:port
    SSHSession s;
    QString remaining = input;

    int atIdx = remaining.indexOf('@');
    if (atIdx >= 0) {
        s.username = remaining.left(atIdx);
        remaining = remaining.mid(atIdx + 1);
    }

    int colonIdx = remaining.lastIndexOf(':');
    if (colonIdx >= 0) {
        bool ok;
        int port = remaining.mid(colonIdx + 1).toInt(&ok);
        if (ok) {
            s.port = port;
            remaining = remaining.left(colonIdx);
        }
    }

    s.host = remaining;
    if (!s.host.isEmpty())
        m_tabManager->newSSHTab(s, input);
}

void MainWindow::onUpdateAvailable(const QString &version, const QString &url,
                                    const QString &changelog, const QString &sha256,
                                    qint64 size)
{
    QString text = QStringLiteral("SOSterm %1 is available.").arg(version);
    if (!changelog.isEmpty())
        text += QStringLiteral("\n\n%1").arg(changelog);
    text += QStringLiteral("\n\nWould you like to update now?");

    QMessageBox msgBox(this);
    msgBox.setWindowTitle("Update Available");
    msgBox.setText(text);
    msgBox.setIcon(QMessageBox::Information);
    auto *updateBtn = msgBox.addButton("Update Now", QMessageBox::AcceptRole);
    msgBox.addButton("Later", QMessageBox::RejectRole);
    msgBox.exec();

    if (msgBox.clickedButton() != updateBtn)
        return;

    // Create progress dialog
    m_progressDialog = new QProgressDialog("Downloading update...", "Cancel", 0, 100, this);
    m_progressDialog->setWindowTitle("Updating SOSterm");
    m_progressDialog->setWindowModality(Qt::WindowModal);
    m_progressDialog->setMinimumDuration(0);
    m_progressDialog->setValue(0);
    m_progressDialog->setAutoClose(false);
    m_progressDialog->setAutoReset(false);

    // Connect progress signals
    connect(m_updateChecker, &UpdateChecker::downloadProgress,
            this, [this](qint64 received, qint64 total) {
        if (m_progressDialog) {
            if (total > 0) {
                m_progressDialog->setMaximum(100);
                int pct = static_cast<int>((received * 100) / total);
                m_progressDialog->setValue(pct);
                m_progressDialog->setLabelText(
                    QStringLiteral("Downloading update... %1 MB / %2 MB")
                        .arg(received / (1024.0 * 1024.0), 0, 'f', 1)
                        .arg(total / (1024.0 * 1024.0), 0, 'f', 1));
            } else {
                m_progressDialog->setMaximum(0); // indeterminate
                m_progressDialog->setLabelText(
                    QStringLiteral("Downloading update... %1 MB")
                        .arg(received / (1024.0 * 1024.0), 0, 'f', 1));
            }
        }
    });

    connect(m_updateChecker, &UpdateChecker::installReady,
            this, &MainWindow::onInstallReady);
    connect(m_updateChecker, &UpdateChecker::downloadFailed,
            this, &MainWindow::onDownloadFailed);

    // Handle cancel
    connect(m_progressDialog, &QProgressDialog::canceled, this, [this]() {
        m_updateChecker->cancelDownload();
        disconnect(m_updateChecker, &UpdateChecker::downloadProgress, this, nullptr);
        disconnect(m_updateChecker, &UpdateChecker::installReady,
                   this, &MainWindow::onInstallReady);
        disconnect(m_updateChecker, &UpdateChecker::downloadFailed,
                   this, &MainWindow::onDownloadFailed);
        if (m_progressDialog) {
            m_progressDialog->deleteLater();
            m_progressDialog = nullptr;
        }
    });

    // Start the download
    m_updateChecker->downloadAndInstall(url, sha256, size);
}

void MainWindow::onInstallReady(const QString &installerPath)
{
    if (m_progressDialog) {
        m_progressDialog->deleteLater();
        m_progressDialog = nullptr;
    }

    // Disconnect one-shot signals to avoid double-firing on next update check
    disconnect(m_updateChecker, &UpdateChecker::downloadProgress, this, nullptr);
    disconnect(m_updateChecker, &UpdateChecker::installReady,
               this, &MainWindow::onInstallReady);
    disconnect(m_updateChecker, &UpdateChecker::downloadFailed,
               this, &MainWindow::onDownloadFailed);

    // Run install.sh with pkexec for graphical sudo
    bool started = QProcess::startDetached(
        QStringLiteral("pkexec"),
        {installerPath});

    if (!started) {
        QMessageBox::critical(this, "Update Failed",
            "Failed to launch the installer.\n\n"
            "You can install manually by running:\n"
            "  sudo " + installerPath);
        return;
    }

    QMessageBox::information(this, "Update Complete",
        "SOSterm has been updated. Please restart the application.");
}

void MainWindow::onDownloadFailed(const QString &error)
{
    if (m_progressDialog) {
        m_progressDialog->deleteLater();
        m_progressDialog = nullptr;
    }

    // Disconnect one-shot signals
    disconnect(m_updateChecker, &UpdateChecker::downloadProgress, this, nullptr);
    disconnect(m_updateChecker, &UpdateChecker::installReady,
               this, &MainWindow::onInstallReady);
    disconnect(m_updateChecker, &UpdateChecker::downloadFailed,
               this, &MainWindow::onDownloadFailed);

    QMessageBox::critical(this, "Update Failed", error);
}

void MainWindow::updateStatusBar()
{
    auto *term = m_tabManager->currentTerminal();
    if (!term) {
        m_sshInfoLabel->clear();
        m_dimsLabel->clear();
        m_shellLabel->clear();
        m_cwdLabel->clear();
        return;
    }

    // SSH info
    QString sshId = term->property("sshSessionId").toString();
    if (!sshId.isEmpty()) {
        SSHSession s = m_sshStore->getSession(sshId);
        m_sshInfoLabel->setText(QStringLiteral("SSH: %1").arg(s.displayName()));
    } else {
        m_sshInfoLabel->clear();
    }

    // Dimensions
    m_dimsLabel->setText(QStringLiteral("%1x%2")
        .arg(term->screenColumnsCount())
        .arg(term->screenLinesCount()));

    // Shell name
    m_shellLabel->setText(QFileInfo(m_settings->getShell()).fileName());

    // Working directory
    m_cwdLabel->setText(term->workingDirectory());
}

// --- Event filter for Ctrl+C/V and right-click context menu ---

bool MainWindow::eventFilter(QObject *obj, QEvent *event)
{
    if (event->type() == QEvent::KeyPress) {
        auto *ke = static_cast<QKeyEvent *>(event);
        if (ke->modifiers() == Qt::ControlModifier) {
            if (ke->key() == Qt::Key_C && m_hasSelection) {
                onCopy();
                return true;
            }
            if (ke->key() == Qt::Key_V) {
                onPaste();
                return true;
            }
        }
    } else if (event->type() == QEvent::ContextMenu) {
        auto *ce = static_cast<QContextMenuEvent *>(event);
        auto *term = m_tabManager->currentTerminal();
        if (term) {
            bool hasText = !term->selectedText(true).isEmpty();
            QMenu menu;
            auto *copyAction = menu.addAction("Copy", this, &MainWindow::onCopy);
            copyAction->setEnabled(hasText);
            menu.addAction("Paste", this, &MainWindow::onPaste);
            menu.addSeparator();
            menu.addAction("Clear", this, [term]() { term->clear(); });
            menu.addSeparator();
            menu.addAction("Find", this, &MainWindow::onFind);
            menu.exec(ce->globalPos());
            return true;
        }
    }
    return QMainWindow::eventFilter(obj, event);
}

// --- Close ---

void MainWindow::closeEvent(QCloseEvent *event)
{
    // Save sidebar state
    m_sshSidebar->saveExpandedState();

    // Save session
    if (m_settings->get("auto_save_session", true).toBool())
        m_sessionManager.saveSession(m_tabManager);

    // Save geometry
    saveGeometry();

    // Confirm close if processes running
    if (m_settings->get("confirm_close_running", true).toBool()) {
        int running = 0;
        for (int i = 0; i < m_tabManager->count(); ++i) {
            auto *t = qobject_cast<QTermWidget *>(m_tabManager->widget(i));
            if (t) ++running;  // QTermWidget tabs are always "running"
        }
        if (running > 0) {
            auto result = QMessageBox::question(this, "Confirm Exit",
                QStringLiteral("There are %1 active terminal(s). Close anyway?").arg(running),
                QMessageBox::Yes | QMessageBox::No);
            if (result != QMessageBox::Yes) {
                event->ignore();
                return;
            }
        }
    }

    m_tabManager->closeAllTabs();
    event->accept();
}

bool MainWindow::restoreSession()
{
    if (!m_settings->get("restore_session", true).toBool())
        return false;
    return m_sessionManager.restoreSession(m_tabManager);
}

void MainWindow::ensureOneTab(const QString &shell, const QString &cwd)
{
    if (m_tabManager->count() == 0)
        m_tabManager->newTab(shell, cwd);
}

// --- SSH dialog handlers ---

void MainWindow::onEditSession(const SSHSession &session)
{
    SSHSessionDialog dlg(m_sshStore, session, this);
    if (dlg.exec() == QDialog::Accepted) {
        SSHSession s = dlg.result();
        m_sshStore->updateSession(s);
        m_sshSidebar->refresh();
    }
}

void MainWindow::onEditGroup(const SSHGroup &group)
{
    SSHGroupDialog dlg(group, this);
    if (dlg.exec() == QDialog::Accepted) {
        SSHGroup g = dlg.result();
        m_sshStore->updateGroup(g);
        m_sshSidebar->refresh();
    }
}

void MainWindow::onDeleteSession(const SSHSession &session)
{
    auto result = QMessageBox::question(this, "Delete Session",
        QStringLiteral("Delete SSH session \"%1\"?").arg(session.displayName()),
        QMessageBox::Yes | QMessageBox::No);
    if (result == QMessageBox::Yes) {
        m_sshStore->deleteSession(session.id);
        m_sshSidebar->refresh();
    }
}

void MainWindow::onDeleteGroup(const SSHGroup &group)
{
    auto result = QMessageBox::question(this, "Delete Group",
        QStringLiteral("Delete group \"%1\"? Sessions will be moved to ungrouped.").arg(group.name),
        QMessageBox::Yes | QMessageBox::No);
    if (result == QMessageBox::Yes) {
        m_sshStore->deleteGroup(group.id);
        m_sshSidebar->refresh();
    }
}

void MainWindow::onNewSession()
{
    showSSHConnectDialog();
}

void MainWindow::onNewGroup()
{
    SSHGroupDialog dlg(SSHGroup(), this);
    if (dlg.exec() == QDialog::Accepted) {
        SSHGroup g = dlg.result();
        m_sshStore->addGroup(g);
        m_sshSidebar->refresh();
    }
}

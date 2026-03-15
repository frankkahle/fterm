#include "sessiontabmanager.h"
#include "thememanager.h"

#include <QApplication>
#include <QClipboard>
#include <QDesktopServices>
#include <QDir>
#include <QDirIterator>
#include <QFileInfo>
#include <QMenu>
#include <QProcess>
#include <QTabBar>
#include <QUrl>
#include <unistd.h>
#include <qtermwidget5/qtermwidget.h>
#include <qtermwidget5/Emulation.h>

SessionTabManager::SessionTabManager(Settings *settings, QWidget *parent)
    : QTabWidget(parent)
    , m_settings(settings)
{
    setTabsClosable(true);
    setMovable(true);
    setDocumentMode(true);

    tabBar()->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(tabBar(), &QWidget::customContextMenuRequested,
            this, &SessionTabManager::showTabContextMenu);
    connect(this, &QTabWidget::tabCloseRequested,
            this, [this](int index) { closeTab(index); });
    connect(this, &QTabWidget::currentChanged,
            this, &SessionTabManager::onCurrentChanged);
}

QTermWidget *SessionTabManager::createTerminal()
{
    auto *term = new QTermWidget(0, this);
    configureTerminal(term);
    return term;
}

void SessionTabManager::configureTerminal(QTermWidget *term)
{
    // Font
    QFont font(m_settings->get("font_family", "Monospace").toString());
    font.setPointSize(m_settings->get("font_size", 11).toInt());
    term->setTerminalFont(font);

    // Scrollback
    term->setHistorySize(m_settings->get("scrollback_lines", 10000).toInt());

    // Cursor
    QString cursorStyle = m_settings->get("cursor_style", "block").toString();
    if (cursorStyle == "underline")
        term->setKeyboardCursorShape(Konsole::Emulation::KeyboardCursorShape::UnderlineCursor);
    else if (cursorStyle == "bar")
        term->setKeyboardCursorShape(Konsole::Emulation::KeyboardCursorShape::IBeamCursor);
    else
        term->setKeyboardCursorShape(Konsole::Emulation::KeyboardCursorShape::BlockCursor);

    term->setBlinkingCursor(m_settings->get("cursor_blink", true).toBool());

    // Margin/padding
    term->setMargin(m_settings->get("terminal_padding", 4).toInt());

    // Scrollbar
    term->setScrollBarPosition(QTermWidget::ScrollBarRight);

    // Color scheme
    QString themeName = m_settings->get("theme", "Dark").toString();
    ThemeInfo ti = ThemeManager::theme(themeName);
    term->setColorScheme(ti.colorSchemeName);

    // QTermWidget::setEnvironment() replaces the child environment entirely,
    // so we must pass the full system environment with our overrides applied.
    QStringList env;
    bool hasAuthSock = false;
    bool hasLang = false;
    for (const QString &entry : QProcess::systemEnvironment()) {
        if (entry.startsWith("TERM=") || entry.startsWith("COLORTERM=")
            || entry.startsWith("CLAUDECODE="))
            continue;
        if (entry.startsWith("SSH_AUTH_SOCK="))
            hasAuthSock = true;
        if (entry.startsWith("LANG="))
            hasLang = true;
        env << entry;
    }
    env << "TERM=xterm-256color" << "COLORTERM=truecolor";
    if (!hasLang)
        env << "LANG=en_US.UTF-8";

    // Auto-detect SSH agent socket if not inherited.
    // The agent socket is a Unix domain socket, not a regular file,
    // so we must use QDir::System to match it.
    if (!hasAuthSock) {
        QString found;
        uid_t uid = getuid();
        // Check /tmp/ssh-*/agent.*
        QDirIterator dirIt("/tmp", {"ssh-*"}, QDir::Dirs | QDir::NoDotAndDotDot);
        while (dirIt.hasNext()) {
            QString sshDir = dirIt.next();
            QDirIterator agentIt(sshDir, {"agent.*"},
                                 QDir::Files | QDir::System | QDir::NoDotAndDotDot);
            while (agentIt.hasNext()) {
                QString path = agentIt.next();
                QFileInfo fi(path);
                if (fi.ownerId() == uid) {
                    found = path;
                    break;
                }
            }
            if (!found.isEmpty()) break;
        }
        if (!found.isEmpty())
            env << "SSH_AUTH_SOCK=" + found;
    }

    term->setEnvironment(env);

    term->setAutoClose(false);
    term->setFlowControlEnabled(true);

    // Zoom level
    int zoom = m_settings->get("zoom_level", 0).toInt();
    for (int i = 0; i < zoom; ++i)
        term->zoomIn();
    for (int i = 0; i > zoom; --i)
        term->zoomOut();
}

QTermWidget *SessionTabManager::newTab(const QString &shell, const QString &cwd)
{
    auto *term = createTerminal();

    QString shellPath = shell.isEmpty() ? m_settings->getShell() : shell;
    term->setShellProgram(shellPath);

    if (!cwd.isEmpty())
        term->setWorkingDirectory(cwd);

    term->startShellProgram();
    ++m_tabCounter;

    connect(term, &QTermWidget::finished, this, &SessionTabManager::onTerminalFinished);
    connect(term, &QTermWidget::titleChanged, this, &SessionTabManager::onTitleChanged);
    connect(term, &QTermWidget::urlActivated, this, [](const QUrl &url, bool) {
        QDesktopServices::openUrl(url);
    });

    QString tabTitle2 = QStringLiteral("Term %1").arg(m_tabCounter);
    int idx = addTab(term, tabTitle2);
    setCurrentIndex(idx);

    emit tabCountChanged(count());
    return term;
}

QTermWidget *SessionTabManager::newSSHTab(const SSHSession &session, const QString &tabTitle)
{
    auto *term = createTerminal();

    QString defaultKey = m_settings->get("default_ssh_identity_file").toString();
    QStringList args = session.buildSSHArgs(defaultKey);

    term->setShellProgram("ssh");
    term->setArgs(args);

    term->startShellProgram();
    ++m_tabCounter;

    term->setProperty("sshSessionId", session.id);

    connect(term, &QTermWidget::finished, this, &SessionTabManager::onTerminalFinished);
    connect(term, &QTermWidget::titleChanged, this, &SessionTabManager::onTitleChanged);
    connect(term, &QTermWidget::urlActivated, this, [](const QUrl &url, bool) {
        QDesktopServices::openUrl(url);
    });

    QString title = tabTitle.isEmpty() ? session.displayName() : tabTitle;
    int idx = addTab(term, title);
    setCurrentIndex(idx);

    emit tabCountChanged(count());
    return term;
}

bool SessionTabManager::closeTab(int index)
{
    if (index < 0)
        index = currentIndex();
    if (index < 0 || index >= count())
        return false;

    auto *term = qobject_cast<QTermWidget *>(widget(index));
    if (term) {
        // Disconnect signals before closing
        term->disconnect(this);
    }
    removeTab(index);
    if (term)
        term->deleteLater();

    emit tabCountChanged(count());
    return true;
}

void SessionTabManager::closeAllTabs()
{
    while (count() > 0)
        closeTab(0);
}

void SessionTabManager::closeOtherTabs(int index)
{
    // Close tabs after the kept one first, then before
    for (int i = count() - 1; i > index; --i)
        closeTab(i);
    for (int i = index - 1; i >= 0; --i)
        closeTab(i);
}

QTermWidget *SessionTabManager::currentTerminal() const
{
    return qobject_cast<QTermWidget *>(currentWidget());
}

void SessionTabManager::onCurrentChanged(int index)
{
    auto *term = qobject_cast<QTermWidget *>(widget(index));
    emit currentTerminalChanged(term);
    if (term)
        term->setFocus();
}

void SessionTabManager::onTerminalFinished()
{
    auto *term = qobject_cast<QTermWidget *>(sender());
    if (!term)
        return;
    int idx = indexOf(term);
    if (idx >= 0)
        closeTab(idx);
}

void SessionTabManager::onTitleChanged()
{
    auto *term = qobject_cast<QTermWidget *>(sender());
    if (!term)
        return;
    int idx = indexOf(term);
    if (idx >= 0) {
        QString title = term->title();
        setTabToolTip(idx, title);
        if (idx == currentIndex())
            emit terminalTitleChanged(title);
    }
}

void SessionTabManager::showTabContextMenu(const QPoint &pos)
{
    int idx = tabBar()->tabAt(pos);
    if (idx < 0)
        return;

    QMenu menu;
    menu.addAction("Close", this, [this, idx]() { closeTab(idx); });
    if (count() > 1)
        menu.addAction("Close Others", this, [this, idx]() { closeOtherTabs(idx); });
    menu.addSeparator();
    menu.addAction("New Tab", this, [this]() { newTab(); });
    if (count() > 1)
        menu.addAction("Close All", this, [this]() { closeAllTabs(); });

    // Copy working directory
    auto *term = qobject_cast<QTermWidget *>(widget(idx));
    if (term) {
        menu.addSeparator();
        menu.addAction("Copy Working Directory", this, [term]() {
            QString cwd = term->workingDirectory();
            if (!cwd.isEmpty())
                QApplication::clipboard()->setText(cwd);
        });
    }

    menu.exec(tabBar()->mapToGlobal(pos));
}

QJsonObject SessionTabManager::getSessionData() const
{
    QJsonArray tabs;
    for (int i = 0; i < count(); ++i) {
        auto *term = qobject_cast<QTermWidget *>(widget(i));
        if (!term)
            continue;
        QJsonObject tab;
        tab["cwd"] = term->workingDirectory();
        tab["title"] = tabText(i);
        QString sshId = term->property("sshSessionId").toString();
        if (!sshId.isEmpty())
            tab["ssh_session_id"] = sshId;
        tabs.append(tab);
    }
    QJsonObject data;
    data["tabs"] = tabs;
    data["active_index"] = currentIndex();
    return data;
}

void SessionTabManager::restoreSessionData(const QJsonObject &data)
{
    QJsonArray tabs = data["tabs"].toArray();
    for (const auto &val : tabs) {
        QJsonObject tab = val.toObject();
        QString sshId = tab["ssh_session_id"].toString();

        if (!sshId.isEmpty() && m_sshStore) {
            SSHSession session = m_sshStore->getSession(sshId);
            if (!session.id.isEmpty()) {
                newSSHTab(session);
                continue;
            }
        }

        QString cwd = tab["cwd"].toString();
        newTab(QString(), cwd);
    }

    int activeIdx = data["active_index"].toInt(0);
    if (activeIdx >= 0 && activeIdx < count())
        setCurrentIndex(activeIdx);
}

void SessionTabManager::setSSHStore(SSHSessionStore *store)
{
    m_sshStore = store;
}

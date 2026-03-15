#include "sshsidebar.h"

#include <QHBoxLayout>
#include <QLabel>
#include <QMenu>
#include <QVBoxLayout>

SSHSidebarPanel::SSHSidebarPanel(SSHSessionStore *store, QWidget *parent)
    : QWidget(parent)
    , m_store(store)
{
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(4, 4, 4, 4);
    layout->setSpacing(4);

    // Header
    auto *header = new QLabel("SSH Sessions");
    QFont headerFont = header->font();
    headerFont.setBold(true);
    header->setFont(headerFont);
    layout->addWidget(header);

    // Quick connect bar
    auto *quickLayout = new QHBoxLayout;
    quickLayout->setSpacing(2);
    m_quickEdit = new QLineEdit;
    m_quickEdit->setPlaceholderText("user@host:port");
    auto *connectBtn = new QPushButton("Connect");
    connectBtn->setFixedWidth(60);
    quickLayout->addWidget(m_quickEdit);
    quickLayout->addWidget(connectBtn);
    layout->addLayout(quickLayout);

    connect(m_quickEdit, &QLineEdit::returnPressed, this, &SSHSidebarPanel::onQuickConnect);
    connect(connectBtn, &QPushButton::clicked, this, &SSHSidebarPanel::onQuickConnect);

    // Tree
    m_tree = new QTreeWidget;
    m_tree->setHeaderHidden(true);
    m_tree->setContextMenuPolicy(Qt::CustomContextMenu);
    m_tree->setIndentation(16);
    layout->addWidget(m_tree, 1);

    connect(m_tree, &QTreeWidget::itemDoubleClicked,
            this, &SSHSidebarPanel::onItemDoubleClicked);
    connect(m_tree, &QTreeWidget::customContextMenuRequested,
            this, &SSHSidebarPanel::showContextMenu);

    // Bottom buttons
    auto *btnLayout = new QHBoxLayout;
    auto *newSessionBtn = new QPushButton("+ Session");
    auto *newGroupBtn = new QPushButton("+ Group");
    btnLayout->addWidget(newSessionBtn);
    btnLayout->addWidget(newGroupBtn);
    layout->addLayout(btnLayout);

    connect(newSessionBtn, &QPushButton::clicked,
            this, &SSHSidebarPanel::newSessionRequested);
    connect(newGroupBtn, &QPushButton::clicked,
            this, &SSHSidebarPanel::newGroupRequested);

    refresh();
}

void SSHSidebarPanel::refresh()
{
    // Save expand state before rebuild
    QSet<QString> expandedIds;
    for (int i = 0; i < m_tree->topLevelItemCount(); ++i) {
        auto *item = m_tree->topLevelItem(i);
        if (item->isExpanded())
            expandedIds.insert(item->data(0, Qt::UserRole + 1).toString());
    }

    m_tree->clear();

    // Add groups
    for (const auto &group : m_store->groups()) {
        auto *groupItem = new QTreeWidgetItem(m_tree);
        groupItem->setText(0, group.name);
        groupItem->setData(0, Qt::UserRole, "group");
        groupItem->setData(0, Qt::UserRole + 1, group.id);
        QFont f = groupItem->font(0);
        f.setBold(true);
        groupItem->setFont(0, f);

        if (!group.color.isEmpty())
            groupItem->setForeground(0, QColor(group.color));

        // Sessions in this group
        for (const auto &session : m_store->sessionsInGroup(group.id)) {
            auto *sessionItem = new QTreeWidgetItem(groupItem);
            sessionItem->setText(0, session.displayName());
            sessionItem->setData(0, Qt::UserRole, "session");
            sessionItem->setData(0, Qt::UserRole + 1, session.id);
            if (!session.color.isEmpty())
                sessionItem->setForeground(0, QColor(session.color));
        }

        // Restore expand state
        bool shouldExpand = expandedIds.contains(group.id) || group.expanded;
        groupItem->setExpanded(shouldExpand);
    }

    // Ungrouped sessions
    for (const auto &session : m_store->ungroupedSessions()) {
        auto *item = new QTreeWidgetItem(m_tree);
        item->setText(0, session.displayName());
        item->setData(0, Qt::UserRole, "session");
        item->setData(0, Qt::UserRole + 1, session.id);
        if (!session.color.isEmpty())
            item->setForeground(0, QColor(session.color));
    }
}

void SSHSidebarPanel::saveExpandedState()
{
    for (int i = 0; i < m_tree->topLevelItemCount(); ++i) {
        auto *item = m_tree->topLevelItem(i);
        QString type = item->data(0, Qt::UserRole).toString();
        if (type != "group")
            continue;
        QString groupId = item->data(0, Qt::UserRole + 1).toString();
        SSHGroup g = m_store->getGroup(groupId);
        if (!g.id.isEmpty()) {
            g.expanded = item->isExpanded();
            m_store->updateGroup(g);
        }
    }
}

void SSHSidebarPanel::onItemDoubleClicked(QTreeWidgetItem *item, int)
{
    if (!item)
        return;
    QString type = item->data(0, Qt::UserRole).toString();
    if (type != "session")
        return;
    QString sessionId = item->data(0, Qt::UserRole + 1).toString();
    SSHSession s = m_store->getSession(sessionId);
    if (!s.id.isEmpty())
        emit connectRequested(s);
}

void SSHSidebarPanel::onQuickConnect()
{
    QString text = m_quickEdit->text().trimmed();
    if (!text.isEmpty()) {
        emit quickConnectRequested(text);
        m_quickEdit->clear();
    }
}

void SSHSidebarPanel::showContextMenu(const QPoint &pos)
{
    QMenu menu;
    auto *item = m_tree->itemAt(pos);

    if (item) {
        QString type = item->data(0, Qt::UserRole).toString();
        QString id = item->data(0, Qt::UserRole + 1).toString();

        if (type == "session") {
            SSHSession s = m_store->getSession(id);
            if (!s.id.isEmpty()) {
                menu.addAction("Connect", this, [this, s]() { emit connectRequested(s); });
                menu.addAction("Edit", this, [this, s]() { emit editSessionRequested(s); });
                menu.addAction("Delete", this, [this, s]() { emit deleteSessionRequested(s); });
                menu.addSeparator();
            }
        } else if (type == "group") {
            SSHGroup g = m_store->getGroup(id);
            if (!g.id.isEmpty()) {
                menu.addAction("Edit Group", this, [this, g]() { emit editGroupRequested(g); });
                menu.addAction("Delete Group", this, [this, g]() { emit deleteGroupRequested(g); });
                menu.addSeparator();
            }
        }
    }

    menu.addAction("New Session...", this, [this]() { emit newSessionRequested(); });
    menu.addAction("New Group...", this, [this]() { emit newGroupRequested(); });

    menu.exec(m_tree->mapToGlobal(pos));
}

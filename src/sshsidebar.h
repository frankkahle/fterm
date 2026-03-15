#ifndef SOSTERM_SSHSIDEBAR_H
#define SOSTERM_SSHSIDEBAR_H

#include <QWidget>
#include <QTreeWidget>
#include <QLineEdit>
#include <QPushButton>

#include "sshsessionstore.h"

class SSHSidebarPanel : public QWidget
{
    Q_OBJECT

public:
    explicit SSHSidebarPanel(SSHSessionStore *store, QWidget *parent = nullptr);

    void refresh();
    void saveExpandedState();

signals:
    void connectRequested(const SSHSession &session);
    void quickConnectRequested(const QString &input);
    void editSessionRequested(const SSHSession &session);
    void editGroupRequested(const SSHGroup &group);
    void deleteSessionRequested(const SSHSession &session);
    void deleteGroupRequested(const SSHGroup &group);
    void newSessionRequested();
    void newGroupRequested();

private slots:
    void onItemDoubleClicked(QTreeWidgetItem *item, int column);
    void onQuickConnect();
    void showContextMenu(const QPoint &pos);

private:
    SSHSessionStore *m_store;
    QTreeWidget *m_tree;
    QLineEdit *m_quickEdit;
};

#endif // SOSTERM_SSHSIDEBAR_H

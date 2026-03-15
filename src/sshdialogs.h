#ifndef SOSTERM_SSHDIALOGS_H
#define SOSTERM_SSHDIALOGS_H

#include <QDialog>
#include <QComboBox>
#include <QLineEdit>
#include <QListWidget>
#include <QPushButton>
#include <QSpinBox>

#include "sshsessionstore.h"

class SSHSessionDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SSHSessionDialog(SSHSessionStore *store,
                              const SSHSession &session = SSHSession(),
                              QWidget *parent = nullptr);

    SSHSession result() const;

private slots:
    void onAuthMethodChanged(const QString &method);
    void browseIdentityFile();
    void validate();

private:
    SSHSession m_session;
    QLineEdit *m_nameEdit;
    QLineEdit *m_hostEdit;
    QSpinBox *m_portSpin;
    QLineEdit *m_usernameEdit;
    QComboBox *m_authCombo;
    QLineEdit *m_identityEdit;
    QPushButton *m_browseBtn;
    QLineEdit *m_startupEdit;
    QComboBox *m_groupCombo;
    SSHSessionStore *m_store;
};

class SSHGroupDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SSHGroupDialog(const SSHGroup &group = SSHGroup(),
                            QWidget *parent = nullptr);

    SSHGroup result() const;

private slots:
    void pickColor();
    void validate();

private:
    SSHGroup m_group;
    QLineEdit *m_nameEdit;
    QWidget *m_colorPreview;
    QString m_color;
};

class SSHImportDialog : public QDialog
{
    Q_OBJECT

public:
    explicit SSHImportDialog(const QVector<SSHSession> &candidates,
                             const QString &label,
                             QWidget *parent = nullptr);

    QVector<SSHSession> selectedSessions() const;

private:
    QVector<SSHSession> m_candidates;
    QListWidget *m_list;
};

#endif // SOSTERM_SSHDIALOGS_H

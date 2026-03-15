#ifndef SOSTERM_SSHSESSIONSTORE_H
#define SOSTERM_SSHSESSIONSTORE_H

#include <QObject>
#include <QString>
#include <QStringList>
#include <QVector>

struct SSHSession {
    QString id;
    QString groupId;
    QString name;
    QString host;
    int port = 22;
    QString username;
    QString authMethod;      // "key" or "password"
    QString identityFile;
    QString startupCommand;
    QString color;

    QString displayName() const;
    QStringList buildSSHArgs(const QString &defaultKey = QString()) const;
};

struct SSHGroup {
    QString id;
    QString name;
    QString color;
    bool expanded = true;
};

class SSHSessionStore : public QObject
{
    Q_OBJECT

public:
    explicit SSHSessionStore(const QString &path = QString(), QObject *parent = nullptr);

    void load();
    void save();

    // Groups
    QVector<SSHGroup> groups() const;
    SSHGroup getGroup(const QString &groupId) const;
    void addGroup(const SSHGroup &group);
    void updateGroup(const SSHGroup &group);
    void deleteGroup(const QString &groupId);

    // Sessions
    QVector<SSHSession> sessions() const;
    SSHSession getSession(const QString &sessionId) const;
    QVector<SSHSession> sessionsInGroup(const QString &groupId) const;
    QVector<SSHSession> ungroupedSessions() const;
    void addSession(const SSHSession &session);
    void updateSession(const SSHSession &session);
    void deleteSession(const QString &sessionId);

    // Import
    QVector<SSHSession> importSSHConfig(const QString &configPath = QString());
    QVector<SSHSession> importRemmina(const QString &remminaDir = QString());

    static QString generateId(const QString &prefix);

private:
    QString m_path;
    QVector<SSHGroup> m_groups;
    QVector<SSHSession> m_sessions;
};

#endif // SOSTERM_SSHSESSIONSTORE_H

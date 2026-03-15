#include "sshsessionstore.h"
#include "settings.h"

#include <QDir>
#include <QFile>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QSettings>
#include <QUuid>

// --- SSHSession ---

QString SSHSession::displayName() const
{
    if (!name.isEmpty())
        return name;
    QString label;
    if (!username.isEmpty())
        label = username + "@";
    label += host;
    if (port != 0 && port != 22)
        label += ":" + QString::number(port);
    return label;
}

QStringList SSHSession::buildSSHArgs(const QString &defaultKey) const
{
    QStringList args;
    if (port != 0 && port != 22)
        args << "-p" << QString::number(port);

    QString identity = identityFile.isEmpty() ? defaultKey : identityFile;
    if (!identity.isEmpty()) {
        QString expanded = identity;
        if (expanded.startsWith("~/"))
            expanded = QDir::homePath() + expanded.mid(1);
        args << "-i" << expanded;
    }

    QString target = username.isEmpty() ? host : (username + "@" + host);
    args << target;

    if (!startupCommand.isEmpty())
        args << startupCommand;

    return args;
}

// --- SSHSessionStore ---

SSHSessionStore::SSHSessionStore(const QString &path, QObject *parent)
    : QObject(parent)
    , m_path(path.isEmpty() ? Settings::configDir() + "/ssh_sessions.json" : path)
{
    load();
}

QString SSHSessionStore::generateId(const QString &prefix)
{
    return prefix + "-" + QUuid::createUuid().toString(QUuid::Id128).left(12);
}

void SSHSessionStore::load()
{
    m_groups.clear();
    m_sessions.clear();

    QFile file(m_path);
    if (!file.open(QIODevice::ReadOnly))
        return;

    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    if (!doc.isObject())
        return;

    QJsonObject root = doc.object();

    for (const auto &val : root["groups"].toArray()) {
        QJsonObject obj = val.toObject();
        SSHGroup g;
        g.id = obj["id"].toString();
        g.name = obj["name"].toString();
        g.color = obj["color"].toString();
        g.expanded = obj.value("expanded").toBool(true);
        m_groups.append(g);
    }

    for (const auto &val : root["sessions"].toArray()) {
        QJsonObject obj = val.toObject();
        SSHSession s;
        s.id = obj["id"].toString();
        s.groupId = obj["group_id"].toString();
        s.name = obj["name"].toString();
        s.host = obj["host"].toString();
        s.port = obj.value("port").toInt(22);
        s.username = obj["username"].toString();
        s.authMethod = obj["auth_method"].toString();
        s.identityFile = obj["identity_file"].toString();
        s.startupCommand = obj["startup_command"].toString();
        s.color = obj["color"].toString();
        m_sessions.append(s);
    }
}

void SSHSessionStore::save()
{
    QDir().mkpath(QFileInfo(m_path).absolutePath());

    QJsonArray groupsArr;
    for (const auto &g : m_groups) {
        QJsonObject obj;
        obj["id"] = g.id;
        obj["name"] = g.name;
        obj["color"] = g.color;
        obj["expanded"] = g.expanded;
        groupsArr.append(obj);
    }

    QJsonArray sessionsArr;
    for (const auto &s : m_sessions) {
        QJsonObject obj;
        obj["id"] = s.id;
        obj["group_id"] = s.groupId;
        obj["name"] = s.name;
        obj["host"] = s.host;
        obj["port"] = s.port;
        obj["username"] = s.username;
        obj["auth_method"] = s.authMethod;
        obj["identity_file"] = s.identityFile;
        obj["startup_command"] = s.startupCommand;
        obj["color"] = s.color;
        sessionsArr.append(obj);
    }

    QJsonObject root;
    root["version"] = 1;
    root["groups"] = groupsArr;
    root["sessions"] = sessionsArr;

    QFile file(m_path);
    if (file.open(QIODevice::WriteOnly))
        file.write(QJsonDocument(root).toJson(QJsonDocument::Indented));
}

// --- Group CRUD ---

QVector<SSHGroup> SSHSessionStore::groups() const { return m_groups; }

SSHGroup SSHSessionStore::getGroup(const QString &groupId) const
{
    for (const auto &g : m_groups)
        if (g.id == groupId) return g;
    return {};
}

void SSHSessionStore::addGroup(const SSHGroup &group)
{
    SSHGroup g = group;
    if (g.id.isEmpty())
        g.id = generateId("g");
    m_groups.append(g);
    save();
}

void SSHSessionStore::updateGroup(const SSHGroup &group)
{
    for (auto &g : m_groups) {
        if (g.id == group.id) {
            g = group;
            save();
            return;
        }
    }
}

void SSHSessionStore::deleteGroup(const QString &groupId)
{
    // Move sessions in this group to ungrouped
    for (auto &s : m_sessions) {
        if (s.groupId == groupId)
            s.groupId.clear();
    }
    m_groups.erase(std::remove_if(m_groups.begin(), m_groups.end(),
        [&](const SSHGroup &g) { return g.id == groupId; }), m_groups.end());
    save();
}

// --- Session CRUD ---

QVector<SSHSession> SSHSessionStore::sessions() const { return m_sessions; }

SSHSession SSHSessionStore::getSession(const QString &sessionId) const
{
    for (const auto &s : m_sessions)
        if (s.id == sessionId) return s;
    return {};
}

QVector<SSHSession> SSHSessionStore::sessionsInGroup(const QString &groupId) const
{
    QVector<SSHSession> result;
    for (const auto &s : m_sessions)
        if (s.groupId == groupId) result.append(s);
    return result;
}

QVector<SSHSession> SSHSessionStore::ungroupedSessions() const
{
    QVector<SSHSession> result;
    for (const auto &s : m_sessions)
        if (s.groupId.isEmpty()) result.append(s);
    return result;
}

void SSHSessionStore::addSession(const SSHSession &session)
{
    SSHSession s = session;
    if (s.id.isEmpty())
        s.id = generateId("s");
    m_sessions.append(s);
    save();
}

void SSHSessionStore::updateSession(const SSHSession &session)
{
    for (auto &s : m_sessions) {
        if (s.id == session.id) {
            s = session;
            save();
            return;
        }
    }
}

void SSHSessionStore::deleteSession(const QString &sessionId)
{
    m_sessions.erase(std::remove_if(m_sessions.begin(), m_sessions.end(),
        [&](const SSHSession &s) { return s.id == sessionId; }), m_sessions.end());
    save();
}

// --- Import SSH Config ---

QVector<SSHSession> SSHSessionStore::importSSHConfig(const QString &configPath)
{
    QString path = configPath.isEmpty()
        ? QDir::homePath() + "/.ssh/config" : configPath;

    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text))
        return {};

    QVector<SSHSession> candidates;
    SSHSession current;
    bool inHost = false;

    while (!file.atEnd()) {
        QString line = QString::fromUtf8(file.readLine()).trimmed();
        if (line.isEmpty() || line.startsWith('#'))
            continue;

        int sep = line.indexOf(QRegExp("\\s+"));
        if (sep < 0) continue;
        QString key = line.left(sep).toLower();
        QString value = line.mid(sep).trimmed();

        if (key == "host") {
            if (inHost && !current.host.isEmpty())
                candidates.append(current);
            current = SSHSession();
            inHost = true;
            // Skip wildcard hosts
            if (value.contains('*') || value.contains('?')) {
                inHost = false;
                continue;
            }
            current.name = value;
        } else if (inHost) {
            if (key == "hostname")
                current.host = value;
            else if (key == "port")
                current.port = value.toInt();
            else if (key == "user")
                current.username = value;
            else if (key == "identityfile") {
                current.identityFile = value;
                current.authMethod = "key";
            }
        }
    }
    if (inHost && !current.host.isEmpty())
        candidates.append(current);

    // If host wasn't explicitly set, use the Host alias
    for (auto &s : candidates) {
        if (s.host.isEmpty())
            s.host = s.name;
    }

    // Deduplicate against existing sessions
    QVector<SSHSession> result;
    for (auto &c : candidates) {
        bool dup = false;
        for (const auto &existing : m_sessions) {
            if (existing.host == c.host && existing.port == c.port
                && existing.username == c.username) {
                dup = true;
                break;
            }
        }
        if (!dup)
            result.append(c);
    }
    return result;
}

// --- Import Remmina ---

QVector<SSHSession> SSHSessionStore::importRemmina(const QString &remminaDir)
{
    QStringList searchDirs;
    if (remminaDir.isEmpty()) {
        searchDirs << QDir::homePath() + "/.local/share/remmina"
                   << QDir::homePath() + "/.remmina";
    } else {
        searchDirs << remminaDir;
    }

    QVector<SSHSession> candidates;

    for (const auto &dirPath : searchDirs) {
        QDir dir(dirPath);
        if (!dir.exists())
            continue;

        for (const auto &entry : dir.entryInfoList({"*.remmina"}, QDir::Files)) {
            QSettings ini(entry.absoluteFilePath(), QSettings::IniFormat);
            ini.beginGroup("remmina");

            QString protocol = ini.value("protocol").toString().toUpper();
            if (protocol != "SSH")
                continue;

            SSHSession s;
            s.name = ini.value("name").toString();

            QString server = ini.value("server").toString();
            // Parse host:port
            int colonIdx = server.lastIndexOf(':');
            if (colonIdx > 0) {
                bool ok;
                int port = server.mid(colonIdx + 1).toInt(&ok);
                if (ok) {
                    s.host = server.left(colonIdx);
                    s.port = port;
                } else {
                    s.host = server;
                }
            } else {
                s.host = server;
            }

            s.username = ini.value("username").toString();
            QString keyFile = ini.value("ssh_privatekey").toString();
            if (!keyFile.isEmpty()) {
                s.identityFile = keyFile;
                s.authMethod = "key";
            }
            s.startupCommand = ini.value("exec").toString();

            ini.endGroup();

            if (!s.host.isEmpty())
                candidates.append(s);
        }
    }

    // Deduplicate
    QVector<SSHSession> result;
    for (auto &c : candidates) {
        bool dup = false;
        for (const auto &existing : m_sessions) {
            if (existing.host == c.host && existing.port == c.port
                && existing.username == c.username) {
                dup = true;
                break;
            }
        }
        if (!dup)
            result.append(c);
    }
    return result;
}

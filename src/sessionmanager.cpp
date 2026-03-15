#include "sessionmanager.h"
#include "sessiontabmanager.h"
#include "settings.h"

#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>

QString SessionManager::sessionFilePath()
{
    return Settings::configDir() + "/session.json";
}

void SessionManager::saveSession(SessionTabManager *tabManager)
{
    QDir().mkpath(Settings::configDir());
    QJsonObject data = tabManager->getSessionData();
    QFile file(sessionFilePath());
    if (file.open(QIODevice::WriteOnly))
        file.write(QJsonDocument(data).toJson(QJsonDocument::Indented));
}

bool SessionManager::restoreSession(SessionTabManager *tabManager)
{
    QFile file(sessionFilePath());
    if (!file.open(QIODevice::ReadOnly))
        return false;

    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    if (!doc.isObject())
        return false;

    QJsonObject data = doc.object();
    if (data["tabs"].toArray().isEmpty())
        return false;

    tabManager->restoreSessionData(data);
    return true;
}

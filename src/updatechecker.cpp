#include "updatechecker.h"
#include "settings.h"

#include <QDateTime>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>

static const char *UPDATE_URL = "https://sos-tech.ca/updates/fterm/latest.json";
static const int COOLDOWN_SECS = 86400; // 24 hours

UpdateChecker::UpdateChecker(Settings *settings, const QString &currentVersion,
                             QObject *parent)
    : QObject(parent)
    , m_nam(new QNetworkAccessManager(this))
    , m_settings(settings)
    , m_currentVersion(currentVersion)
{
}

bool UpdateChecker::shouldAutoCheck() const
{
    qint64 last = m_settings->get("last_update_check", 0).toLongLong();
    qint64 now = QDateTime::currentSecsSinceEpoch();
    return (now - last) >= COOLDOWN_SECS;
}

void UpdateChecker::check(bool recordTime)
{
    m_recordTime = recordTime;

    QNetworkRequest req{QUrl(QString::fromLatin1(UPDATE_URL))};
    req.setHeader(QNetworkRequest::UserAgentHeader,
                  QStringLiteral("SOSterm/%1").arg(m_currentVersion));

    auto *reply = m_nam->get(req);
    connect(reply, &QNetworkReply::finished, this, &UpdateChecker::onReplyFinished);
}

void UpdateChecker::autoCheck()
{
    if (shouldAutoCheck())
        check(true);
}

void UpdateChecker::onReplyFinished()
{
    auto *reply = qobject_cast<QNetworkReply *>(sender());
    if (!reply)
        return;
    reply->deleteLater();

    if (m_recordTime)
        m_settings->set("last_update_check",
                        (qlonglong)QDateTime::currentSecsSinceEpoch());

    if (reply->error() != QNetworkReply::NoError) {
        emit checkFinished(false);
        return;
    }

    QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
    if (!doc.isObject()) {
        emit checkFinished(false);
        return;
    }

    QJsonObject obj = doc.object();
    QString remoteVersion = obj["version"].toString();
    QString downloadUrl = obj["download_url"].toString();
    QString changelog = obj["changelog"].toString();

    if (isNewer(m_currentVersion, remoteVersion)) {
        emit updateAvailable(remoteVersion, downloadUrl, changelog);
        emit checkFinished(true);
    } else {
        emit checkFinished(false);
    }
}

bool UpdateChecker::isNewer(const QString &current, const QString &remote)
{
    auto parse = [](const QString &v) -> QVector<int> {
        QVector<int> parts;
        for (const auto &s : v.split('.'))
            parts.append(s.toInt());
        return parts;
    };

    QVector<int> cur = parse(current);
    QVector<int> rem = parse(remote);

    int len = qMax(cur.size(), rem.size());
    for (int i = 0; i < len; ++i) {
        int c = i < cur.size() ? cur[i] : 0;
        int r = i < rem.size() ? rem[i] : 0;
        if (r > c) return true;
        if (r < c) return false;
    }
    return false;
}

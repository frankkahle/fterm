#include "updatechecker.h"
#include "settings.h"

#include <QCryptographicHash>
#include <QDateTime>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QProcess>

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
    QString sha256 = obj["sha256"].toString();
    qint64 size = obj["size"].toDouble();  // JSON numbers -> double -> qint64

    if (isNewer(m_currentVersion, remoteVersion)) {
        emit updateAvailable(remoteVersion, downloadUrl, changelog, sha256, size);
        emit checkFinished(true);
    } else {
        emit checkFinished(false);
    }
}

// --- Download and install ---

void UpdateChecker::downloadAndInstall(const QString &url, const QString &sha256,
                                        qint64 expectedSize)
{
    m_downloadSha256 = sha256;
    m_downloadExpectedSize = expectedSize;

    // Create temp directory for download
    m_downloadDir = QDir::tempPath() + QStringLiteral("/sosterm-update");
    QDir dir(m_downloadDir);
    if (dir.exists())
        dir.removeRecursively();
    dir.mkpath(".");

    // Derive filename from URL
    QUrl qurl(url);
    QString filename = qurl.fileName();
    if (filename.isEmpty())
        filename = QStringLiteral("SOSterm-update.tar.gz");
    m_downloadFilePath = m_downloadDir + "/" + filename;

    QNetworkRequest req{qurl};
    req.setHeader(QNetworkRequest::UserAgentHeader,
                  QStringLiteral("SOSterm/%1").arg(m_currentVersion));

    m_downloadReply = m_nam->get(req);
    connect(m_downloadReply, &QNetworkReply::downloadProgress,
            this, &UpdateChecker::onDownloadProgress);
    connect(m_downloadReply, &QNetworkReply::finished,
            this, &UpdateChecker::onDownloadFinished);
}

void UpdateChecker::cancelDownload()
{
    if (m_downloadReply) {
        m_downloadReply->abort();
        m_downloadReply->deleteLater();
        m_downloadReply = nullptr;
    }
    if (!m_downloadDir.isEmpty()) {
        QDir(m_downloadDir).removeRecursively();
        m_downloadDir.clear();
    }
}

void UpdateChecker::onDownloadProgress(qint64 received, qint64 total)
{
    // If server doesn't provide Content-Length, use our expected size
    if (total <= 0 && m_downloadExpectedSize > 0)
        total = m_downloadExpectedSize;
    emit downloadProgress(received, total);
}

void UpdateChecker::onDownloadFinished()
{
    if (!m_downloadReply)
        return;

    m_downloadReply->deleteLater();

    if (m_downloadReply->error() != QNetworkReply::NoError) {
        QString error = m_downloadReply->errorString();
        m_downloadReply = nullptr;
        QDir(m_downloadDir).removeRecursively();
        emit downloadFailed(QStringLiteral("Download failed: %1").arg(error));
        return;
    }

    // Write downloaded data to file
    QByteArray data = m_downloadReply->readAll();
    m_downloadReply = nullptr;

    QFile file(m_downloadFilePath);
    if (!file.open(QIODevice::WriteOnly)) {
        QDir(m_downloadDir).removeRecursively();
        emit downloadFailed(QStringLiteral("Failed to write download: %1").arg(file.errorString()));
        return;
    }
    file.write(data);
    file.close();

    // Verify SHA256
    if (!m_downloadSha256.isEmpty()) {
        QCryptographicHash hash(QCryptographicHash::Sha256);
        hash.addData(data);
        QString actualHash = hash.result().toHex();
        if (actualHash != m_downloadSha256) {
            QDir(m_downloadDir).removeRecursively();
            emit downloadFailed(QStringLiteral(
                "SHA256 verification failed.\nExpected: %1\nGot: %2")
                .arg(m_downloadSha256, actualHash));
            return;
        }
    }

    // Extract tarball
    QProcess tarProcess;
    tarProcess.setWorkingDirectory(m_downloadDir);
    tarProcess.start(QStringLiteral("tar"),
                     {QStringLiteral("xzf"), m_downloadFilePath,
                      QStringLiteral("-C"), m_downloadDir});

    if (!tarProcess.waitForFinished(60000)) {
        QDir(m_downloadDir).removeRecursively();
        emit downloadFailed(QStringLiteral("Extraction timed out."));
        return;
    }

    if (tarProcess.exitCode() != 0) {
        QString stderr = tarProcess.readAllStandardError();
        QDir(m_downloadDir).removeRecursively();
        emit downloadFailed(QStringLiteral("Extraction failed: %1").arg(stderr));
        return;
    }

    // Find the install.sh in the extracted directory
    // The tarball extracts to SOSterm-X.Y.Z/ containing install.sh
    QDir extractDir(m_downloadDir);
    QStringList entries = extractDir.entryList(QDir::Dirs | QDir::NoDotAndDotDot);

    QString installerPath;
    for (const auto &entry : entries) {
        QString candidate = m_downloadDir + "/" + entry + "/install.sh";
        if (QFile::exists(candidate)) {
            installerPath = candidate;
            break;
        }
    }

    if (installerPath.isEmpty()) {
        QDir(m_downloadDir).removeRecursively();
        emit downloadFailed(QStringLiteral("install.sh not found in the downloaded archive."));
        return;
    }

    // Make install.sh executable
    QFile::setPermissions(installerPath,
        QFile::permissions(installerPath) | QFileDevice::ExeOwner | QFileDevice::ExeGroup | QFileDevice::ExeOther);

    emit installReady(installerPath);
}

// --- Version comparison ---

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

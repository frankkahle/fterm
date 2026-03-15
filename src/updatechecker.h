#ifndef SOSTERM_UPDATECHECKER_H
#define SOSTERM_UPDATECHECKER_H

#include <QObject>
#include <QString>

class QNetworkAccessManager;
class QNetworkReply;
class Settings;

class UpdateChecker : public QObject
{
    Q_OBJECT

public:
    explicit UpdateChecker(Settings *settings, const QString &currentVersion,
                           QObject *parent = nullptr);

    void check(bool recordTime = true);
    void autoCheck();
    bool shouldAutoCheck() const;

    void downloadAndInstall(const QString &url, const QString &sha256,
                            qint64 expectedSize);
    void cancelDownload();

signals:
    void updateAvailable(const QString &version, const QString &url,
                         const QString &changelog, const QString &sha256,
                         qint64 size);
    void checkFinished(bool hadUpdate);
    void downloadProgress(qint64 received, qint64 total);
    void installReady(const QString &installerPath);
    void downloadFailed(const QString &error);

private slots:
    void onReplyFinished();
    void onDownloadProgress(qint64 received, qint64 total);
    void onDownloadFinished();

private:
    static bool isNewer(const QString &current, const QString &remote);

    QNetworkAccessManager *m_nam;
    Settings *m_settings;
    QString m_currentVersion;
    bool m_recordTime = true;

    // Download state
    QNetworkReply *m_downloadReply = nullptr;
    QString m_downloadSha256;
    qint64 m_downloadExpectedSize = 0;
    QString m_downloadDir;
    QString m_downloadFilePath;
};

#endif // SOSTERM_UPDATECHECKER_H

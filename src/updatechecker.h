#ifndef SOSTERM_UPDATECHECKER_H
#define SOSTERM_UPDATECHECKER_H

#include <QObject>
#include <QString>

class QNetworkAccessManager;
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

signals:
    void updateAvailable(const QString &version, const QString &url, const QString &changelog);
    void checkFinished(bool hadUpdate);

private slots:
    void onReplyFinished();

private:
    static bool isNewer(const QString &current, const QString &remote);

    QNetworkAccessManager *m_nam;
    Settings *m_settings;
    QString m_currentVersion;
    bool m_recordTime = true;
};

#endif // SOSTERM_UPDATECHECKER_H

#ifndef SOSTERM_SETTINGS_H
#define SOSTERM_SETTINGS_H

#include <QObject>
#include <QJsonObject>
#include <QVariant>
#include <QString>

class Settings : public QObject
{
    Q_OBJECT

public:
    explicit Settings(QObject *parent = nullptr);

    QVariant get(const QString &key, const QVariant &defaultValue = QVariant()) const;
    void set(const QString &key, const QVariant &value);
    QString getShell() const;

    static QString configDir();
    static QString configFilePath();

signals:
    void settingsChanged(const QString &key, const QVariant &value);

private:
    void load();
    void save();
    void ensureDefaults();

    QJsonObject m_data;
    static QJsonObject s_defaults;
    static QJsonObject initDefaults();
};

#endif // SOSTERM_SETTINGS_H

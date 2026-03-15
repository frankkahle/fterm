#include "settings.h"

#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QProcessEnvironment>
#include <QStandardPaths>

QJsonObject Settings::s_defaults = Settings::initDefaults();

QJsonObject Settings::initDefaults()
{
    QJsonObject d;
    d["font_family"] = "Monospace";
    d["font_size"] = 11;
    d["theme"] = "Dark";
    d["scrollback_lines"] = 10000;
    d["cursor_style"] = "block";
    d["cursor_blink"] = true;
    d["shell"] = "";
    d["confirm_close_running"] = true;
    d["auto_save_session"] = true;
    d["restore_session"] = true;
    d["window_geometry"] = "";
    d["window_state"] = "";
    d["zoom_level"] = 0;
    d["terminal_padding"] = 4;
    d["last_update_check"] = 0;
    d["default_ssh_identity_file"] = "";
    return d;
}

Settings::Settings(QObject *parent)
    : QObject(parent)
{
    load();
}

QString Settings::configDir()
{
    return QStandardPaths::writableLocation(QStandardPaths::GenericConfigLocation) + "/SOSterm";
}

QString Settings::configFilePath()
{
    return configDir() + "/settings.json";
}

void Settings::load()
{
    QFile file(configFilePath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        if (doc.isObject())
            m_data = doc.object();
    }
    ensureDefaults();
}

void Settings::save()
{
    QDir().mkpath(configDir());
    QFile file(configFilePath());
    if (file.open(QIODevice::WriteOnly)) {
        file.write(QJsonDocument(m_data).toJson(QJsonDocument::Indented));
    }
}

void Settings::ensureDefaults()
{
    for (auto it = s_defaults.constBegin(); it != s_defaults.constEnd(); ++it) {
        if (!m_data.contains(it.key()))
            m_data[it.key()] = it.value();
    }
}

QVariant Settings::get(const QString &key, const QVariant &defaultValue) const
{
    if (m_data.contains(key))
        return m_data.value(key).toVariant();
    if (s_defaults.contains(key))
        return s_defaults.value(key).toVariant();
    return defaultValue;
}

void Settings::set(const QString &key, const QVariant &value)
{
    m_data[key] = QJsonValue::fromVariant(value);
    save();
    emit settingsChanged(key, value);
}

QString Settings::getShell() const
{
    QString shell = get("shell").toString();
    if (!shell.isEmpty())
        return shell;
    shell = QProcessEnvironment::systemEnvironment().value("SHELL");
    if (!shell.isEmpty())
        return shell;
    return "/bin/bash";
}

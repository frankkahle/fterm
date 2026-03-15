#ifndef SOSTERM_PREFERENCESDIALOG_H
#define SOSTERM_PREFERENCESDIALOG_H

#include <QCheckBox>
#include <QComboBox>
#include <QDialog>
#include <QFontComboBox>
#include <QLineEdit>
#include <QSpinBox>

#include "settings.h"

class PreferencesDialog : public QDialog
{
    Q_OBJECT

public:
    explicit PreferencesDialog(Settings *settings, QWidget *parent = nullptr);

private slots:
    void apply();
    void browseSSHKey();

private:
    QWidget *createGeneralTab();
    QWidget *createAppearanceTab();
    QWidget *createSessionTab();

    Settings *m_settings;

    // General
    QLineEdit *m_shellEdit;
    QSpinBox *m_scrollbackSpin;
    QCheckBox *m_confirmCloseCheck;

    // Appearance
    QComboBox *m_themeCombo;
    QFontComboBox *m_fontCombo;
    QSpinBox *m_fontSizeSpin;
    QComboBox *m_cursorStyleCombo;
    QCheckBox *m_cursorBlinkCheck;
    QSpinBox *m_paddingSpin;

    // Session
    QCheckBox *m_autoSaveCheck;
    QCheckBox *m_restoreCheck;
    QLineEdit *m_sshKeyEdit;
};

#endif // SOSTERM_PREFERENCESDIALOG_H

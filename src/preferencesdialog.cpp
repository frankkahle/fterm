#include "preferencesdialog.h"
#include "thememanager.h"

#include <QDialogButtonBox>
#include <QDir>
#include <QFileDialog>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QPushButton>
#include <QTabWidget>
#include <QVBoxLayout>

PreferencesDialog::PreferencesDialog(Settings *settings, QWidget *parent)
    : QDialog(parent)
    , m_settings(settings)
{
    setWindowTitle("Preferences");
    setMinimumSize(450, 400);

    auto *layout = new QVBoxLayout(this);

    auto *tabs = new QTabWidget;
    tabs->addTab(createGeneralTab(), "General");
    tabs->addTab(createAppearanceTab(), "Appearance");
    tabs->addTab(createSessionTab(), "Session");
    layout->addWidget(tabs);

    auto *buttons = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel | QDialogButtonBox::Apply);
    connect(buttons, &QDialogButtonBox::accepted, this, [this]() { apply(); accept(); });
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    connect(buttons->button(QDialogButtonBox::Apply), &QPushButton::clicked,
            this, &PreferencesDialog::apply);
    layout->addWidget(buttons);
}

QWidget *PreferencesDialog::createGeneralTab()
{
    auto *tab = new QWidget;
    auto *layout = new QVBoxLayout(tab);

    // Shell
    auto *shellGroup = new QGroupBox("Shell");
    auto *shellLayout = new QFormLayout(shellGroup);
    m_shellEdit = new QLineEdit(m_settings->get("shell").toString());
    m_shellEdit->setPlaceholderText("Leave empty for default ($SHELL)");
    shellLayout->addRow("Shell:", m_shellEdit);
    layout->addWidget(shellGroup);

    // Behavior
    auto *behaviorGroup = new QGroupBox("Behavior");
    auto *behaviorLayout = new QFormLayout(behaviorGroup);

    m_scrollbackSpin = new QSpinBox;
    m_scrollbackSpin->setRange(100, 100000);
    m_scrollbackSpin->setSingleStep(1000);
    m_scrollbackSpin->setValue(m_settings->get("scrollback_lines", 10000).toInt());
    behaviorLayout->addRow("Scrollback lines:", m_scrollbackSpin);

    m_confirmCloseCheck = new QCheckBox("Confirm close when processes are running");
    m_confirmCloseCheck->setChecked(m_settings->get("confirm_close_running", true).toBool());
    behaviorLayout->addRow(m_confirmCloseCheck);

    layout->addWidget(behaviorGroup);
    layout->addStretch();
    return tab;
}

QWidget *PreferencesDialog::createAppearanceTab()
{
    auto *tab = new QWidget;
    auto *layout = new QVBoxLayout(tab);

    // Theme
    auto *themeGroup = new QGroupBox("Theme");
    auto *themeLayout = new QFormLayout(themeGroup);
    m_themeCombo = new QComboBox;
    m_themeCombo->addItems(ThemeManager::themeNames());
    m_themeCombo->setCurrentText(m_settings->get("theme", "Dark").toString());
    themeLayout->addRow("Theme:", m_themeCombo);
    layout->addWidget(themeGroup);

    // Font
    auto *fontGroup = new QGroupBox("Font");
    auto *fontLayout = new QFormLayout(fontGroup);
    m_fontCombo = new QFontComboBox;
    m_fontCombo->setCurrentFont(QFont(m_settings->get("font_family", "Monospace").toString()));
    fontLayout->addRow("Family:", m_fontCombo);

    m_fontSizeSpin = new QSpinBox;
    m_fontSizeSpin->setRange(6, 72);
    m_fontSizeSpin->setValue(m_settings->get("font_size", 11).toInt());
    fontLayout->addRow("Size:", m_fontSizeSpin);
    layout->addWidget(fontGroup);

    // Cursor
    auto *cursorGroup = new QGroupBox("Cursor");
    auto *cursorLayout = new QFormLayout(cursorGroup);
    m_cursorStyleCombo = new QComboBox;
    m_cursorStyleCombo->addItems({"block", "underline", "bar"});
    m_cursorStyleCombo->setCurrentText(m_settings->get("cursor_style", "block").toString());
    cursorLayout->addRow("Style:", m_cursorStyleCombo);

    m_cursorBlinkCheck = new QCheckBox("Blink cursor");
    m_cursorBlinkCheck->setChecked(m_settings->get("cursor_blink", true).toBool());
    cursorLayout->addRow(m_cursorBlinkCheck);
    layout->addWidget(cursorGroup);

    // Terminal
    auto *termGroup = new QGroupBox("Terminal");
    auto *termLayout = new QFormLayout(termGroup);
    m_paddingSpin = new QSpinBox;
    m_paddingSpin->setRange(0, 32);
    m_paddingSpin->setSingleStep(2);
    m_paddingSpin->setValue(m_settings->get("terminal_padding", 4).toInt());
    termLayout->addRow("Padding:", m_paddingSpin);
    layout->addWidget(termGroup);

    layout->addStretch();
    return tab;
}

QWidget *PreferencesDialog::createSessionTab()
{
    auto *tab = new QWidget;
    auto *layout = new QVBoxLayout(tab);

    // Session
    auto *sessionGroup = new QGroupBox("Session");
    auto *sessionLayout = new QFormLayout(sessionGroup);

    m_autoSaveCheck = new QCheckBox("Auto-save session on exit");
    m_autoSaveCheck->setChecked(m_settings->get("auto_save_session", true).toBool());
    sessionLayout->addRow(m_autoSaveCheck);

    m_restoreCheck = new QCheckBox("Restore previous session on startup");
    m_restoreCheck->setChecked(m_settings->get("restore_session", true).toBool());
    sessionLayout->addRow(m_restoreCheck);
    layout->addWidget(sessionGroup);

    // SSH
    auto *sshGroup = new QGroupBox("SSH");
    auto *sshLayout = new QFormLayout(sshGroup);

    auto *keyLayout = new QHBoxLayout;
    m_sshKeyEdit = new QLineEdit(m_settings->get("default_ssh_identity_file").toString());
    m_sshKeyEdit->setPlaceholderText("Default identity file for all SSH sessions");
    auto *browseBtn = new QPushButton("Browse...");
    keyLayout->addWidget(m_sshKeyEdit);
    keyLayout->addWidget(browseBtn);
    sshLayout->addRow("Default SSH Key:", keyLayout);
    connect(browseBtn, &QPushButton::clicked, this, &PreferencesDialog::browseSSHKey);
    layout->addWidget(sshGroup);

    layout->addStretch();
    return tab;
}

void PreferencesDialog::apply()
{
    m_settings->set("shell", m_shellEdit->text().trimmed());
    m_settings->set("scrollback_lines", m_scrollbackSpin->value());
    m_settings->set("confirm_close_running", m_confirmCloseCheck->isChecked());
    m_settings->set("theme", m_themeCombo->currentText());
    m_settings->set("font_family", m_fontCombo->currentFont().family());
    m_settings->set("font_size", m_fontSizeSpin->value());
    m_settings->set("cursor_style", m_cursorStyleCombo->currentText());
    m_settings->set("cursor_blink", m_cursorBlinkCheck->isChecked());
    m_settings->set("terminal_padding", m_paddingSpin->value());
    m_settings->set("auto_save_session", m_autoSaveCheck->isChecked());
    m_settings->set("restore_session", m_restoreCheck->isChecked());
    m_settings->set("default_ssh_identity_file", m_sshKeyEdit->text().trimmed());
}

void PreferencesDialog::browseSSHKey()
{
    QString path = QFileDialog::getOpenFileName(
        this, "Select SSH Key", QDir::homePath() + "/.ssh");
    if (!path.isEmpty())
        m_sshKeyEdit->setText(path);
}

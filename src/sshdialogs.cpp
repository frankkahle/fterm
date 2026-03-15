#include "sshdialogs.h"

#include <QColorDialog>
#include <QDialogButtonBox>
#include <QDir>
#include <QFileDialog>
#include <QFormLayout>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QLabel>
#include <QMessageBox>
#include <QVBoxLayout>

// --- SSHSessionDialog ---

SSHSessionDialog::SSHSessionDialog(SSHSessionStore *store,
                                   const SSHSession &session,
                                   QWidget *parent)
    : QDialog(parent)
    , m_session(session)
    , m_store(store)
{
    setWindowTitle(session.id.isEmpty() ? "New SSH Session" : "Edit SSH Session");
    setMinimumWidth(400);

    auto *layout = new QVBoxLayout(this);
    auto *form = new QFormLayout;

    m_nameEdit = new QLineEdit(session.name);
    m_nameEdit->setPlaceholderText("Optional display name");
    form->addRow("Name:", m_nameEdit);

    m_hostEdit = new QLineEdit(session.host);
    form->addRow("Host:", m_hostEdit);

    m_portSpin = new QSpinBox;
    m_portSpin->setRange(1, 65535);
    m_portSpin->setValue(session.port > 0 ? session.port : 22);
    form->addRow("Port:", m_portSpin);

    m_usernameEdit = new QLineEdit(session.username);
    form->addRow("Username:", m_usernameEdit);

    m_authCombo = new QComboBox;
    m_authCombo->addItems({"key", "password"});
    if (!session.authMethod.isEmpty())
        m_authCombo->setCurrentText(session.authMethod);
    form->addRow("Auth Method:", m_authCombo);

    auto *identityLayout = new QHBoxLayout;
    m_identityEdit = new QLineEdit(session.identityFile);
    m_browseBtn = new QPushButton("Browse...");
    identityLayout->addWidget(m_identityEdit);
    identityLayout->addWidget(m_browseBtn);
    form->addRow("Identity File:", identityLayout);

    m_startupEdit = new QLineEdit(session.startupCommand);
    m_startupEdit->setPlaceholderText("Optional command to run after connect");
    form->addRow("Startup Cmd:", m_startupEdit);

    m_groupCombo = new QComboBox;
    m_groupCombo->addItem("(None)", QString());
    for (const auto &g : store->groups())
        m_groupCombo->addItem(g.name, g.id);
    if (!session.groupId.isEmpty()) {
        int idx = m_groupCombo->findData(session.groupId);
        if (idx >= 0) m_groupCombo->setCurrentIndex(idx);
    }
    form->addRow("Group:", m_groupCombo);

    layout->addLayout(form);

    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttons, &QDialogButtonBox::accepted, this, &SSHSessionDialog::validate);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    layout->addWidget(buttons);

    connect(m_authCombo, &QComboBox::currentTextChanged,
            this, &SSHSessionDialog::onAuthMethodChanged);
    connect(m_browseBtn, &QPushButton::clicked,
            this, &SSHSessionDialog::browseIdentityFile);

    onAuthMethodChanged(m_authCombo->currentText());
}

void SSHSessionDialog::onAuthMethodChanged(const QString &method)
{
    bool isKey = (method == "key");
    m_identityEdit->setEnabled(isKey);
    m_browseBtn->setEnabled(isKey);
}

void SSHSessionDialog::browseIdentityFile()
{
    QString path = QFileDialog::getOpenFileName(
        this, "Select SSH Key", QDir::homePath() + "/.ssh");
    if (!path.isEmpty())
        m_identityEdit->setText(path);
}

void SSHSessionDialog::validate()
{
    if (m_hostEdit->text().trimmed().isEmpty()) {
        QMessageBox::warning(this, "Validation", "Host is required.");
        m_hostEdit->setFocus();
        return;
    }
    accept();
}

SSHSession SSHSessionDialog::result() const
{
    SSHSession s = m_session;
    s.name = m_nameEdit->text().trimmed();
    s.host = m_hostEdit->text().trimmed();
    s.port = m_portSpin->value();
    s.username = m_usernameEdit->text().trimmed();
    s.authMethod = m_authCombo->currentText();
    s.identityFile = m_identityEdit->text().trimmed();
    s.startupCommand = m_startupEdit->text().trimmed();
    s.groupId = m_groupCombo->currentData().toString();
    return s;
}

// --- SSHGroupDialog ---

SSHGroupDialog::SSHGroupDialog(const SSHGroup &group, QWidget *parent)
    : QDialog(parent)
    , m_group(group)
    , m_color(group.color)
{
    setWindowTitle(group.id.isEmpty() ? "New SSH Group" : "Edit SSH Group");
    setMinimumWidth(350);

    auto *layout = new QVBoxLayout(this);
    auto *form = new QFormLayout;

    m_nameEdit = new QLineEdit(group.name);
    form->addRow("Name:", m_nameEdit);

    auto *colorLayout = new QHBoxLayout;
    m_colorPreview = new QWidget;
    m_colorPreview->setFixedSize(24, 24);
    m_colorPreview->setStyleSheet(
        QStringLiteral("background-color: %1; border: 1px solid #666;")
            .arg(m_color.isEmpty() ? "#666666" : m_color));
    auto *colorBtn = new QPushButton("Pick Color...");
    colorLayout->addWidget(m_colorPreview);
    colorLayout->addWidget(colorBtn);
    colorLayout->addStretch();
    form->addRow("Color:", colorLayout);

    layout->addLayout(form);

    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttons, &QDialogButtonBox::accepted, this, &SSHGroupDialog::validate);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    layout->addWidget(buttons);

    connect(colorBtn, &QPushButton::clicked, this, &SSHGroupDialog::pickColor);
}

void SSHGroupDialog::pickColor()
{
    QColor initial = m_color.isEmpty() ? QColor("#666666") : QColor(m_color);
    QColor c = QColorDialog::getColor(initial, this, "Pick Group Color");
    if (c.isValid()) {
        m_color = c.name();
        m_colorPreview->setStyleSheet(
            QStringLiteral("background-color: %1; border: 1px solid #666;").arg(m_color));
    }
}

void SSHGroupDialog::validate()
{
    if (m_nameEdit->text().trimmed().isEmpty()) {
        QMessageBox::warning(this, "Validation", "Group name is required.");
        m_nameEdit->setFocus();
        return;
    }
    accept();
}

SSHGroup SSHGroupDialog::result() const
{
    SSHGroup g = m_group;
    g.name = m_nameEdit->text().trimmed();
    g.color = m_color;
    return g;
}

// --- SSHImportDialog ---

SSHImportDialog::SSHImportDialog(const QVector<SSHSession> &candidates,
                                 const QString &label,
                                 QWidget *parent)
    : QDialog(parent)
    , m_candidates(candidates)
{
    setWindowTitle("Import SSH Sessions");
    setMinimumWidth(450);
    setMinimumHeight(350);

    auto *layout = new QVBoxLayout(this);
    layout->addWidget(new QLabel(label));

    m_list = new QListWidget;
    for (const auto &s : candidates) {
        auto *item = new QListWidgetItem(s.displayName());
        item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
        item->setCheckState(Qt::Checked);
        m_list->addItem(item);
    }
    layout->addWidget(m_list, 1);

    auto *selectLayout = new QHBoxLayout;
    auto *selectAllBtn = new QPushButton("Select All");
    auto *deselectAllBtn = new QPushButton("Deselect All");
    selectLayout->addWidget(selectAllBtn);
    selectLayout->addWidget(deselectAllBtn);
    selectLayout->addStretch();
    layout->addLayout(selectLayout);

    connect(selectAllBtn, &QPushButton::clicked, this, [this]() {
        for (int i = 0; i < m_list->count(); ++i)
            m_list->item(i)->setCheckState(Qt::Checked);
    });
    connect(deselectAllBtn, &QPushButton::clicked, this, [this]() {
        for (int i = 0; i < m_list->count(); ++i)
            m_list->item(i)->setCheckState(Qt::Unchecked);
    });

    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    buttons->button(QDialogButtonBox::Ok)->setText("Import");
    connect(buttons, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    layout->addWidget(buttons);
}

QVector<SSHSession> SSHImportDialog::selectedSessions() const
{
    QVector<SSHSession> selected;
    for (int i = 0; i < m_list->count(); ++i) {
        if (m_list->item(i)->checkState() == Qt::Checked && i < m_candidates.size())
            selected.append(m_candidates[i]);
    }
    return selected;
}

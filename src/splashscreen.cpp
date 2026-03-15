#include "splashscreen.h"

#include <QApplication>
#include <QEasingCurve>
#include <QFontMetrics>
#include <QLinearGradient>
#include <QPainter>
#include <QPainterPath>
#include <QScreen>
#include <QTimer>

static const int SPLASH_W = 420;
static const int SPLASH_H = 360;

static const QColor BRAND_BLUE("#0047FF");
static const QColor TEXT_DARK("#2c2c2c");
static const QColor TEXT_MID("#6e7a8a");
static const QColor TEXT_LIGHT("#8a94a0");
static const QColor BORDER_COLOR("#c0c8d4");
static const QColor LOADER_TRACK("#d0d5dd");
static const QColor GRAD_TOP("#f5f7fa");
static const QColor GRAD_BOTTOM("#e8ecf1");

SplashScreen::SplashScreen(const QString &version, QWidget *parent)
    : QWidget(parent, Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint | Qt::Tool)
    , m_version(version)
{
    setAttribute(Qt::WA_TranslucentBackground);
    setFixedSize(SPLASH_W, SPLASH_H);

    // Center on screen
    if (auto *screen = QApplication::primaryScreen()) {
        QRect geo = screen->availableGeometry();
        move(geo.center() - rect().center());
    }

    // Load logo
    m_logo = QPixmap(":/resources/sos-logo.png");
    if (m_logo.isNull())
        m_logo = QPixmap("/opt/SOSterm/resources/sos-logo.png");
    if (!m_logo.isNull() && m_logo.width() > 180)
        m_logo = m_logo.scaledToWidth(180, Qt::SmoothTransformation);

    startAnimations();
}

void SplashScreen::setStatus(const QString &text)
{
    m_status = text;
    update();
}

QPropertyAnimation *SplashScreen::makeFade(const QByteArray &prop, int delay)
{
    auto *anim = new QPropertyAnimation(this, prop, this);
    anim->setDuration(600);
    anim->setStartValue(0.0);
    anim->setEndValue(1.0);
    anim->setEasingCurve(QEasingCurve::OutCubic);
    QTimer::singleShot(delay, anim, [anim]() { anim->start(); });
    return anim;
}

void SplashScreen::startAnimations()
{
    makeFade("fadeLogo", 0);
    makeFade("fadeName", 200);
    makeFade("fadeTagline", 400);
    makeFade("fadeLoader", 600);
    makeFade("fadeUrl", 800);
    makeFade("fadeVersion", 1000);

    // Bouncing loader
    auto *loader = new QPropertyAnimation(this, "loaderPos", this);
    loader->setDuration(1400);
    loader->setStartValue(0.0);
    loader->setEndValue(1.0);
    loader->setEasingCurve(QEasingCurve::InOutSine);
    loader->setLoopCount(-1);
    loader->start();
}

void SplashScreen::paintEvent(QPaintEvent *)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing);
    p.setRenderHint(QPainter::SmoothPixmapTransform);

    // Background
    QLinearGradient grad(0, 0, 0, SPLASH_H);
    grad.setColorAt(0, GRAD_TOP);
    grad.setColorAt(1, GRAD_BOTTOM);

    QPainterPath bgPath;
    bgPath.addRoundedRect(QRectF(0, 0, SPLASH_W, SPLASH_H), 10, 10);
    p.fillPath(bgPath, grad);
    p.setPen(QPen(BORDER_COLOR, 1));
    p.drawPath(bgPath);

    int y = 50;

    // Logo
    if (!m_logo.isNull()) {
        qreal slideOffset = 8.0 * (1.0 - m_fadeLogo);
        p.setOpacity(m_fadeLogo);
        int logoX = (SPLASH_W - m_logo.width()) / 2;
        p.drawPixmap(logoX, (int)(y + slideOffset), m_logo);
        p.setOpacity(1.0);
        y += m_logo.height() + 24;
    } else {
        y += 24;
    }

    // App name: "f" dark + "term" blue
    {
        qreal slideOffset = 8.0 * (1.0 - m_fadeName);
        p.setOpacity(m_fadeName);
        QFont nameFont("Segoe UI", 26, QFont::Bold);
        nameFont.setLetterSpacing(QFont::AbsoluteSpacing, 1.0);
        p.setFont(nameFont);
        QFontMetrics fm(nameFont);

        QString full = "SOSterm";
        int totalW = fm.horizontalAdvance(full);
        int startX = (SPLASH_W - totalW) / 2;
        int nameY = (int)(y + slideOffset);

        p.setPen(TEXT_DARK);
        p.drawText(startX, nameY + fm.ascent(), "SOS");
        int sosW = fm.horizontalAdvance("SOS");
        p.setPen(BRAND_BLUE);
        p.drawText(startX + sosW, nameY + fm.ascent(), "term");

        p.setOpacity(1.0);
        y += 36;
    }

    // Tagline
    {
        qreal slideOffset = 8.0 * (1.0 - m_fadeTagline);
        p.setOpacity(m_fadeTagline);
        QFont tagFont("Segoe UI", 10);
        p.setFont(tagFont);
        p.setPen(TEXT_MID);
        QFontMetrics fm(tagFont);
        QString tag = "by S.O.S. Tech Services";
        int tagX = (SPLASH_W - fm.horizontalAdvance(tag)) / 2;
        p.drawText(tagX, (int)(y + slideOffset) + fm.ascent(), tag);
        p.setOpacity(1.0);
        y += 36;
    }

    // Loading bar
    {
        p.setOpacity(m_fadeLoader);
        int barW = 120, barH = 3, radius = 2;
        int barX = (SPLASH_W - barW) / 2;

        // Track
        p.setPen(Qt::NoPen);
        p.setBrush(LOADER_TRACK);
        p.drawRoundedRect(barX, y, barW, barH, radius, radius);

        // Fill (40% width, bouncing)
        int fillW = (int)(barW * 0.4);
        int travel = barW - fillW;
        qreal pos = m_loaderPos;
        qreal fx = pos < 0.5 ? travel * (pos * 2.0)
                              : travel * ((1.0 - pos) * 2.0);
        p.setBrush(BRAND_BLUE);
        p.setClipRect(barX, y, barW, barH);
        p.drawRoundedRect((int)(barX + fx), y, fillW, barH, radius, radius);
        p.setClipping(false);

        p.setOpacity(1.0);
        y += 16;
    }

    // Status text
    {
        p.setOpacity(m_fadeLoader);
        QFont statusFont("Segoe UI", 9);
        p.setFont(statusFont);
        p.setPen(TEXT_MID);
        QFontMetrics fm(statusFont);
        if (!m_status.isEmpty()) {
            int sx = (SPLASH_W - fm.horizontalAdvance(m_status)) / 2;
            p.drawText(sx, y + fm.ascent(), m_status);
        }
        p.setOpacity(1.0);
        y += 28;
    }

    // URL
    {
        qreal slideOffset = 8.0 * (1.0 - m_fadeUrl);
        p.setOpacity(m_fadeUrl);
        QFont urlFont("Segoe UI", 11, QFont::DemiBold);
        p.setFont(urlFont);
        p.setPen(BRAND_BLUE);
        QFontMetrics fm(urlFont);
        QString url = "sos-tech.ca";
        int ux = (SPLASH_W - fm.horizontalAdvance(url)) / 2;
        p.drawText(ux, (int)(y + slideOffset) + fm.ascent(), url);
        p.setOpacity(1.0);
    }

    // Version (bottom-right)
    {
        p.setOpacity(m_fadeVersion);
        QFont verFont("Segoe UI", 8);
        p.setFont(verFont);
        p.setPen(TEXT_LIGHT);
        QFontMetrics fm(verFont);
        QString ver = "v" + m_version;
        int vx = SPLASH_W - fm.horizontalAdvance(ver) - 15;
        p.drawText(vx, SPLASH_H - 20, ver);
        p.setOpacity(1.0);
    }
}

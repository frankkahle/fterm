#ifndef SOSTERM_SPLASHSCREEN_H
#define SOSTERM_SPLASHSCREEN_H

#include <QWidget>
#include <QPropertyAnimation>

class SplashScreen : public QWidget
{
    Q_OBJECT
    Q_PROPERTY(qreal fadeLogo READ fadeLogo WRITE setFadeLogo)
    Q_PROPERTY(qreal fadeName READ fadeName WRITE setFadeName)
    Q_PROPERTY(qreal fadeTagline READ fadeTagline WRITE setFadeTagline)
    Q_PROPERTY(qreal fadeLoader READ fadeLoader WRITE setFadeLoader)
    Q_PROPERTY(qreal fadeUrl READ fadeUrl WRITE setFadeUrl)
    Q_PROPERTY(qreal fadeVersion READ fadeVersion WRITE setFadeVersion)
    Q_PROPERTY(qreal loaderPos READ loaderPos WRITE setLoaderPos)

public:
    explicit SplashScreen(const QString &version, QWidget *parent = nullptr);

    void setStatus(const QString &text);

    qreal fadeLogo() const { return m_fadeLogo; }
    void setFadeLogo(qreal v) { m_fadeLogo = v; update(); }
    qreal fadeName() const { return m_fadeName; }
    void setFadeName(qreal v) { m_fadeName = v; update(); }
    qreal fadeTagline() const { return m_fadeTagline; }
    void setFadeTagline(qreal v) { m_fadeTagline = v; update(); }
    qreal fadeLoader() const { return m_fadeLoader; }
    void setFadeLoader(qreal v) { m_fadeLoader = v; update(); }
    qreal fadeUrl() const { return m_fadeUrl; }
    void setFadeUrl(qreal v) { m_fadeUrl = v; update(); }
    qreal fadeVersion() const { return m_fadeVersion; }
    void setFadeVersion(qreal v) { m_fadeVersion = v; update(); }
    qreal loaderPos() const { return m_loaderPos; }
    void setLoaderPos(qreal v) { m_loaderPos = v; update(); }

protected:
    void paintEvent(QPaintEvent *event) override;

private:
    void startAnimations();
    QPropertyAnimation *makeFade(const QByteArray &prop, int delay);

    QString m_version;
    QString m_status;
    QPixmap m_logo;

    qreal m_fadeLogo = 0;
    qreal m_fadeName = 0;
    qreal m_fadeTagline = 0;
    qreal m_fadeLoader = 0;
    qreal m_fadeUrl = 0;
    qreal m_fadeVersion = 0;
    qreal m_loaderPos = 0;
};

#endif // SOSTERM_SPLASHSCREEN_H

#ifndef SOSTERM_SESSIONMANAGER_H
#define SOSTERM_SESSIONMANAGER_H

#include <QString>

class SessionTabManager;

class SessionManager
{
public:
    void saveSession(SessionTabManager *tabManager);
    bool restoreSession(SessionTabManager *tabManager);

    static QString sessionFilePath();
};

#endif // SOSTERM_SESSIONMANAGER_H

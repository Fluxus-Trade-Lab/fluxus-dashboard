# GEX Engine — Unattended Setup (IB Gateway + IBC)

The engine tries ports 4001 (Gateway live) → 4002 (Gateway paper) → 7496 (TWS).
It works with **TWS running today**; IB Gateway + IBC makes it fully unattended.

## 0. Manual run (works now, TWS or Gateway up)

```bash
cd /Users/taolezhu/Documents/AI-Trading-System
.venv/bin/python -m pipeline.gex.engine            # pulls, writes data/gex/, commits + pushes
.venv/bin/python -m pipeline.gex.engine --no-push  # same but no git push
.venv/bin/python -m pipeline.gex.engine --no-git   # write files only, no commit
```

Offline plumbing test (no IBKR needed):

```bash
.venv/bin/python -m pipeline.gex.engine --out /tmp/gextest \
  --offline-fixture tests/gex/fixtures/chain_es_20260710.csv --offline-spot 7570 --no-git
```

## 1. Install IB Gateway (stable channel)

Download "IB Gateway — Stable" from interactivebrokers.com → Trading → API.
Install to /Applications. Log in once manually; under Configure → Settings → API:
enable ActiveX/Socket clients, Read-Only API, trusted IP 127.0.0.1, port 4001.

## 2. Install IBC (auto-login / dialog handling)

https://github.com/IbcAlpha/IBC → download the latest macOS release zip,
unzip to /opt/ibc. Edit /opt/ibc/config.ini:

    IbLoginId=<your username>
    IbPassword=<password>            # or leave blank to type once per boot
    TradingMode=live
    AcceptIncomingConnectionAction=accept
    ExistingSessionDetectedAction=primary
    AutoRestartTime=08:35 PM         # before the 21:00 JST run

Then make /opt/ibc/gatewaystartmacos.sh executable and test it: Gateway should
start and log in with no dialogs.

> **Credentials are yours to enter.** Do not commit `config.ini` with a password to
> git. Prefer leaving `IbPassword` blank (type once per boot) if the Mac reboots rarely.

## 3. Keep Gateway alive

Create a second LaunchAgent (com.fluxus.ibgateway.plist) with
KeepAlive=true and RunAtLoad=true pointing at gatewaystartmacos.sh, OR add
Gateway to Login Items. IBC handles the daily re-auth/restart dialogs.

## 4. Install the daily engine job (you run these — a standing scheduled job)

The plist ships in the repo at `scripts/com.fluxus.gex-engine.plist`. Install it:

```bash
chmod +x /Users/taolezhu/Documents/AI-Trading-System/scripts/run_gex_engine.sh
cp /Users/taolezhu/Documents/AI-Trading-System/scripts/com.fluxus.gex-engine.plist \
   ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.fluxus.gex-engine.plist
launchctl list | grep fluxus.gex          # should list com.fluxus.gex-engine
```

Runs weekdays **21:00 JST = 8:00am EDT** (change plist Hour to 22 during US EST).
Logs: `data/gex/engine.log` (gitignored). It coexists with the existing
`com.fluxus.gex-daily` SPX→pine agent — different label, no conflict.

To test the job immediately: `launchctl start com.fluxus.gex-engine`.
To remove it: `launchctl unload ~/Library/LaunchAgents/com.fluxus.gex-engine.plist`.

## 5. Failure behavior

If the pull fails, the engine republishes the last good JSON/brief with
`stale: true` and a red STALE banner, and still commits (the archive records the
gap). Fix = make sure Gateway is up, then rerun manually:

    .venv/bin/python -m pipeline.gex.engine

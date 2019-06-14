import os
import logging
from ib_insync import ibcontroller
from ib_insync import IB
from ib_insync.ibcontroller import Watchdog
import ib_insync.util as util
from updateSecrets import updateSecrets

util.logToConsole(logging.DEBUG)
logger = logging.getLogger(name=__name__)
ibcPath = os.getenv("IBC_PATH", "/opt/ibc")
homePath = os.getenv("HOME", "/root")
twsPath = os.getenv("TWS_PATH", "~/Jts")
twsLiveorPaperMode = os.getenv("TWS_LIVE_PAPER", "paper")
secretsPath = os.getenv("SECRETS_PATH", "/ibc/paper/")
configTemplate = homePath + "/config_template.ini"
config = homePath + "/config.ini"

logger.info("Updating Secrets")
updateSecrets(configTemplate, config, secretsPath=secretsPath)

ibc = ibcontroller.IBC(
    twsVersion=972,
    gateway=True,
    ibcPath=ibcPath,
    tradingMode=twsLiveorPaperMode,
    twsSettingsPath=twsPath,
    ibcIni=config,
)

ibc.start()
ib = IB()
watchdog = Watchdog(
    ibc,
    ib,
    port=4001,
    connectTimeout=59,
    appStartupTime=45,
    appTimeout=59,
    retryDelay=10,
)
watchdog.start()
IB.run()

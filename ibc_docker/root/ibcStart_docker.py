import os
import logging
import json
import base64
import boto3
from ib_insync import Stock, Future, util
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
firehoseStream = os.getenv("FIREHOSE_STREAM_NAME", "ibc-paper")
secretsPath = os.getenv("SECRETS_PATH", "/ibc/paper/")
configTemplate = homePath + "/config_template.ini"
config = homePath + "/config.ini"
# TODO: get region from environment variables
firehose = boto3.client("firehose", region_name="us-east-2")

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

ib.sleep(60)

#TODO: Add this 'setup' to a different event handler to fire when connected
STOCK = [
    "SPY",
    "QQQ",
    "IWM",
    "VXX",
    "GLD",
    "AMZN",
    "GOOG",
    "EFA",
    "EEM",
    "TLT",
    "USO",
    "GDX",
    "GDXJ",
    "XLF",
    "XLE",
    "XLU",
    "XRT",
    "XLK",
    "XME",
    "FXI",
    "EWZ",
    "FB",
    "AAPL",
    "NFLX",
    "MSFT",
    "BABA",
    "INTC",
    "TSLA",
]
FUTURES = ["ES", "NQ", "RTY", "CL", "NG", "ZB", "ZN", "GC", "MXP", "EUR", "JPY", "GBP"]

stockContracts = [Stock(s, "SMART", "USD") for s in STOCK]
ib.qualifyContracts(*stockContracts)

futures = [ib.reqContractDetails(Future(f)) for f in FUTURES]
futuresContracts = [c.contract for f in futures for c in f]
futuresContracts = [
    c
    for c in futuresContracts
    if c.tradingClass == c.symbol and c.lastTradeDateOrContractMonth.startswith("2019")
]

for contract in stockContracts + futuresContracts:
    ib.reqMktData(contract, "", False, False)

def onPendingTickers(tickers):
    ticks = []
    for t in tickers:
        encodedTick = json.dumps(util.tree(t))
        ticks.append({"Data": encodedTick})
    firehose.put_record_batch(DeliveryStreamName=firehoseStream, Records=ticks)


ib.pendingTickersEvent += onPendingTickers

IB.run()

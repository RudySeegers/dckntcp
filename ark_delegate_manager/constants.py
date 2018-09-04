"""
Here I put basic constants related to us as a delegate.
"""
import arkdbtools.config as ark

CUT_OFF_EARLY_ADOPTER = 16247647

PAYOUT_EXCEPTIONS = [
    'AFrdbXnMHSxaVCjMNnUNtNvsVZUvnuVZqm',
    'APc5PwFJFuEqBsV9qeaU6XLn4XLYxPe7zS',
    'AQ9gNYefdLE83GpfTzc1pPyCZgX6KvV9rm',
]

MIN_AMOUNT_DAILY = 2 * ark.ARK
MIN_AMOUNT_WEEKY = 0.5 * ark.ARK
MIN_AMOUNT_MONTHLY = 0.01 * ark.ARK

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY
MONTH = 28 * DAY


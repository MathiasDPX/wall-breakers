import sentry_sdk

from metrics import record_unhandled_block

class DataDomeCookieExpiredError(RuntimeError):
    pass

class OuestFranceDisabledException(RuntimeError):
    pass

class OuestFranceMissingSubscriptionException(RuntimeError):
    pass

class MediapartInvalidLogin(RuntimeError):
    pass

class MediapartDisabledException(RuntimeError):
    pass

class UnhandledBlockError(NotImplementedError):
    pass
    
    
def sentry_block_error(typename:str):
    record_unhandled_block(typename)
    sentry_sdk.capture_exception(
        UnhandledBlockError(f"Block of type `{typename}` isn't handled"),
        level="warning",
    )

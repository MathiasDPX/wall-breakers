import sentry_sdk

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
    print(f"Block `{typename}` isn't handled")
    sentry_sdk.capture_exception(
        UnhandledBlockError(f"Block of type `{typename}` isn't handled"),
        tags={"block_type": typename}
    )
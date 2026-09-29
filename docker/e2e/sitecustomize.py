# The sandbox has no direct internet route. fsspec/aiohttp must use the same
# source-only proxy as urllib/requests; this changes transport, never data.
try:
    import aiohttp
    original=aiohttp.ClientSession.__init__
    def init(self,*args,**kwargs):
        kwargs.setdefault('trust_env',True)
        original(self,*args,**kwargs)
    aiohttp.ClientSession.__init__=init
except ImportError:
    pass

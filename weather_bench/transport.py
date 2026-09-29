"""Wall-clock request deadlines and conservative accounting for unconfirmed requests."""
from contextlib import contextmanager
import signal
import httpx


@contextmanager
def request_deadline(seconds):
    def expired(signum,frame):
        raise httpx.ReadTimeout('Total request deadline exceeded (including keepalive traffic)')
    old=signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old)


def reserve_unconfirmed(ledger,config,model,run_id,body=None):
    prices=config.get('billing_prices',{}).get(model)
    if config.get('unknown_cost_policy')!='reserve' or not prices:
        ledger['uncertain_cost']=True
        return
    # UTF-8 bytes bound ordinary BPE input tokens; extra allowance covers message
    # framing. Double the fixed endpoint rates to allow cache-write/route fees.
    size=sum(len(m['content'].encode()) for m in body['messages']) if body else config['max_context_bytes']
    reserve=2*((size+4096)*prices['prompt']+config['max_output_tokens']*prices['completion'])+.01
    ledger['budget_reserve_usd']=ledger.get('budget_reserve_usd',0)+reserve
    ledger.setdefault('unconfirmed_requests',[]).append({'run_id':run_id,'model':model,'reserve_usd':reserve})
    ledger['uncertain_cost']=False  # bounded, not reconciled; run cost stays unknown
    return reserve
